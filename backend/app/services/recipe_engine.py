"""Motor de recetas (§7).

Flujo: resolver despensa+perfil -> ordenar por caducidad -> caché (hash) ->
LLM (o stub offline) pidiendo JSON estricto -> normalizar costo/ahorro ->
persistir recetas -> guardar caché -> responder.
"""

import hashlib
import json
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hogar import Hogar
from app.models.item_despensa import ItemDespensa
from app.models.receta import EstadoAprobacion, Receta
from app.models.receta_cache import RecetaCache
from app.models.usuario import RolUsuario, Usuario
from app.schemas.recipes import (
    GenerateRequest,
    GenerateResponse,
    ItemDespensaInput,
    RecetaGenerada,
    RecetaLLM,
    RecetasLLM,
)
from app.services.llm_client import generar_con_llm, llm_disponible, modelo_actual

# Ventana para considerar un item "por caducar" (días).
DIAS_POR_CADUCAR = 4


def generar_recetas(
    db: Session, data: GenerateRequest, current: Usuario
) -> GenerateResponse:
    items, restricciones, presupuesto = _resolver_contexto(db, data, current)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La despensa está vacía: envía 'despensa' o un 'hogar_id' con items.",
        )

    items = _ordenar_por_caducidad(items)
    por_caducar = _items_por_caducar(items)
    # Clave de caché = ingredientes + restricciones + n (§7 paso 5). El presupuesto
    # NO entra en la clave: influye en la primera generación de una combinación,
    # no en los aciertos de caché (tradeoff intencional para abaratar la IA, §2).
    clave = _clave_cache(items, restricciones, data.n_recetas)

    # 5. Caché: reusar si la combinación ya se generó.
    cacheada = db.scalar(select(RecetaCache).where(RecetaCache.clave == clave))
    if cacheada is not None:
        cacheada.hits += 1
        db.commit()
        # Recalcula "úsalo primero" contra las fechas de HOY (el payload guardó
        # un snapshot de caducidad que pudo quedar obsoleto).
        recetas = _recalcular_por_caducar(cacheada.payload["recetas"], por_caducar)
        return GenerateResponse(
            recetas=recetas,
            cache_hit=True,
            fuente=cacheada.payload["fuente"],
        )

    # 2-3. Generar: LLM si hay clave para el proveedor; si no, stub (demo offline).
    if llm_disponible():
        try:
            recetas_llm = generar_con_llm(
                ingredientes_txt=_fmt_ingredientes(items),
                restricciones_txt=", ".join(_una_linea(r) for r in restricciones),
                presupuesto_txt=(
                    f"${presupuesto:.2f} MXN" if presupuesto else "no especificado"
                ),
                por_caducar_txt=", ".join(_una_linea(p) for p in por_caducar),
                n=data.n_recetas,
            )
        except Exception as exc:  # noqa: BLE001 — degradar a un 502 controlado
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="El motor de recetas (LLM) no está disponible por ahora.",
            ) from exc
        fuente = f"llm:{modelo_actual()}"
    else:
        recetas_llm = _recetas_stub(items, por_caducar, data.n_recetas)
        fuente = "stub"

    # 4. Normalizar costo/ahorro y limitar al número pedido.
    normalizadas = _normalizar(recetas_llm.recetas, data.n_recetas)

    # Persistir cada receta (queda con id para GET /recipes/{id}).
    generadas: list[RecetaGenerada] = []
    for r in normalizadas:
        receta = Receta(
            titulo=r.titulo,
            pasos=r.pasos,
            ingredientes=r.ingredientes_usados,
            costo_porcion=r.costo_porcion_mxn,
            porciones=r.porciones,
            ahorro_estimado_mxn=r.ahorro_estimado_mxn,
            estado_aprobacion=EstadoAprobacion.borrador,
            autor_id=current.id,
            tags=["ia-generada", "mexicana"],
        )
        db.add(receta)
        db.flush()  # asigna receta.id sin cerrar la transacción
        generadas.append(RecetaGenerada(id=receta.id, **r.model_dump()))

    db.add(
        RecetaCache(
            clave=clave,
            payload={"recetas": [g.model_dump() for g in generadas], "fuente": fuente},
            hits=0,
        )
    )
    db.commit()

    return GenerateResponse(recetas=generadas, cache_hit=False, fuente=fuente)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _resolver_contexto(
    db: Session, data: GenerateRequest, current: Usuario
) -> tuple[list[ItemDespensaInput], list[str], float | None]:
    """Combina lo enviado en línea con lo del hogar (si se pasa hogar_id)."""
    items = list(data.despensa)
    restricciones = list(data.restricciones)
    presupuesto = data.presupuesto_semanal

    if data.hogar_id is not None:
        hogar = db.get(Hogar, data.hogar_id)
        if hogar is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Hogar no encontrado")
        # Ownership: el hogar debe ser del usuario (o admin). RBAC fino llega en Fase 3.
        if hogar.usuario_id != current.id and current.rol != RolUsuario.admin:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "El hogar no pertenece al usuario"
            )
        if not items:
            db_items = db.scalars(
                select(ItemDespensa).where(ItemDespensa.hogar_id == hogar.id)
            ).all()
            items = [
                ItemDespensaInput(
                    nombre=i.nombre,
                    cantidad=i.cantidad,
                    unidad=i.unidad,
                    fecha_caducidad=i.fecha_caducidad,
                )
                for i in db_items
            ]
        if not restricciones:
            restricciones = list(hogar.restricciones or [])
        if presupuesto is None:
            presupuesto = hogar.presupuesto_semanal

    return items, restricciones, presupuesto


def _ordenar_por_caducidad(
    items: list[ItemDespensaInput],
) -> list[ItemDespensaInput]:
    # Lo que caduca antes va primero; los sin fecha, al final.
    return sorted(
        items, key=lambda i: (i.fecha_caducidad is None, i.fecha_caducidad or date.max)
    )


def _items_por_caducar(items: list[ItemDespensaInput]) -> list[str]:
    limite = date.today() + timedelta(days=DIAS_POR_CADUCAR)
    return [i.nombre for i in items if i.fecha_caducidad and i.fecha_caducidad <= limite]


def _una_linea(texto: str, max_len: int = 120) -> str:
    """Colapsa espacios/saltos de línea y trunca (mitiga inyección de prompt)."""
    return " ".join((texto or "").split())[:max_len]


def _fmt_ingredientes(items: list[ItemDespensaInput]) -> str:
    lineas = []
    for i in items:
        nombre = _una_linea(i.nombre)
        unidad = _una_linea(i.unidad or "", max_len=40)
        cad = f", caduca {i.fecha_caducidad.isoformat()}" if i.fecha_caducidad else ""
        if i.cantidad is not None:
            medida = f"{i.cantidad:g} {unidad}".strip()
        else:
            medida = unidad
        extra = f" ({medida})" if medida else ""
        lineas.append(f"- {nombre}{extra}{cad}")
    return "\n".join(lineas)


def _recalcular_por_caducar(recetas: list[dict], por_caducar: list[str]) -> list[dict]:
    """En cache hit: recalcula 'usa_por_caducar' de cada receta contra HOY."""
    pc_low = [(p, p.lower()) for p in por_caducar]
    salida = []
    for r in recetas:
        r = dict(r)
        usados = [u.lower() for u in r.get("ingredientes_usados", [])]
        r["usa_por_caducar"] = [p for p, pl in pc_low if any(pl in u for u in usados)]
        salida.append(r)
    return salida


def _clave_cache(
    items: list[ItemDespensaInput], restricciones: list[str], n: int
) -> str:
    nombres = sorted({i.nombre.strip().lower() for i in items if i.nombre.strip()})
    restr = sorted({r.strip().lower() for r in restricciones if r.strip()})
    base = json.dumps(
        {"ingredientes": nombres, "restricciones": restr, "n": n},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _normalizar(recetas: list[RecetaLLM], n: int) -> list[RecetaLLM]:
    norm = []
    for r in recetas[:n]:
        norm.append(
            RecetaLLM(
                titulo=(r.titulo or "Receta").strip() or "Receta",
                ingredientes_usados=[x.strip() for x in r.ingredientes_usados if x.strip()],
                ingredientes_faltantes=[
                    x.strip() for x in r.ingredientes_faltantes if x.strip()
                ],
                pasos=[p.strip() for p in r.pasos if p.strip()],
                porciones=max(1, r.porciones or 1),
                costo_porcion_mxn=round(max(0.0, float(r.costo_porcion_mxn or 0.0)), 2),
                ahorro_estimado_mxn=round(max(0.0, float(r.ahorro_estimado_mxn or 0.0)), 2),
                usa_por_caducar=[x.strip() for x in r.usa_por_caducar if x.strip()],
            )
        )
    return norm


_PLANTILLAS = [
    "Salteado de {a} a la mexicana",
    "Sopa casera de {a}",
    "Guiso de {a} con arroz",
    "Tacos de {a}",
    "Ensalada tibia de {a}",
]


def _recetas_stub(
    items: list[ItemDespensaInput], por_caducar: list[str], n: int
) -> RecetasLLM:
    """Recetas deterministas para dev/demo sin clave de LLM (fuente='stub')."""
    nombres = [i.nombre for i in items]
    base = por_caducar or nombres or ["temporada"]
    recetas = []
    for k in range(n):
        ingrediente = base[k % len(base)]
        usados = nombres[:3] if nombres else [ingrediente]
        recetas.append(
            RecetaLLM(
                titulo=_PLANTILLAS[k % len(_PLANTILLAS)].format(a=ingrediente),
                ingredientes_usados=usados,
                ingredientes_faltantes=["sal", "aceite"],
                pasos=[
                    f"Pica {ingrediente} y el resto de los ingredientes disponibles.",
                    "Cocina a fuego medio unos 15 minutos.",
                    "Sazona al gusto y sirve caliente.",
                ],
                porciones=2,
                costo_porcion_mxn=round(25.0 + 5 * k, 2),
                ahorro_estimado_mxn=round(12.0 + 3 * k, 2),
                usa_por_caducar=por_caducar[:3],
            )
        )
    return RecetasLLM(recetas=recetas)
