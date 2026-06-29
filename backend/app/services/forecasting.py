"""Servicio de forecasting (Pilar B, §10).

Carga el XGBoost entrenado en ml/models/. Si no existe, usa una heurística
estacional simple para que el endpoint funcione igualmente (fuente="heuristica").

Calcula, por producto del comercio: demanda esperada del periodo, recomendación de
reabasto y flag de riesgo de merma; y una serie diaria total para la gráfica.
"""

import json
import math
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comercio import ProductoInventario, VentaRegistro

# Horizontes
DIAS_SERIE = 14   # serie diaria total (gráfica)
DIAS_PRODUCTO = 7  # demanda por producto (recomendación)
DIAS_HISTORICO = 120  # ventana para estimar el nivel base
_QUINCENA = (14, 15, 16, 29, 30, 31, 1)
_MES_FACTOR = {
    1: 0.95, 2: 0.92, 3: 0.98, 4: 1.0, 5: 1.05, 6: 1.0,
    7: 1.02, 8: 1.0, 9: 1.03, 10: 1.05, 11: 1.1, 12: 1.25,
}
_NIVEL_PRIOR_DEFAULT = 10.0

# Orden de features esperado. DEBE coincidir con ml/train.py (construir_features).
# Se valida contra metadata.json al cargar; si difiere, se cae a heurística.
FEATURES = ["nivel_base", "mes", "semana", "dia_semana", "es_fin_de_semana", "es_quincena"]

_model = None
_meta: dict | None = None
_loaded = False


def _model_dir() -> Path:
    # backend/app/services/forecasting.py -> repo_root/ml/models
    return Path(__file__).resolve().parents[3] / "ml" / "models"


def _load() -> None:
    global _model, _meta, _loaded
    if _loaded:
        return
    _loaded = True
    try:
        import xgboost as xgb

        mpath = _model_dir() / "forecast_xgb.json"
        meta_path = _model_dir() / "metadata.json"
        # Exigimos modelo + metadata + orden de features coincidente. Si algo falta o
        # no concuerda, dejamos _model=None y el servicio usa la heurística (degradación
        # segura, en vez de predecir con un prior/orden equivocado).
        if mpath.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("features") == FEATURES:
                m = xgb.XGBRegressor()
                m.load_model(str(mpath))
                _model = m
                _meta = meta
    except Exception:
        _model = None  # cae a heurística


def fuente() -> str:
    _load()
    return "xgboost" if _model is not None else "heuristica"


def _nivel_prior() -> float:
    _load()
    if _meta and _meta.get("global_mean_nivel"):
        return float(_meta["global_mean_nivel"])
    return _NIVEL_PRIOR_DEFAULT


def _features_row(nivel_base: float, d: date) -> list[float]:
    return [
        float(nivel_base),
        float(d.month),
        float(d.isocalendar().week),
        float(d.weekday()),
        1.0 if d.weekday() >= 5 else 0.0,
        1.0 if d.day in _QUINCENA else 0.0,
    ]


def _predecir_serie(nivel_base: float, dias: list[date]) -> list[float]:
    """Demanda predicha para cada día (mismo orden que `dias`)."""
    _load()
    if _model is not None:
        import numpy as np

        x = np.array([_features_row(nivel_base, d) for d in dias], dtype=float)
        preds = _model.predict(x)
        return [max(0.0, float(p)) for p in preds]
    # Heurística estacional (sin modelo entrenado).
    out = []
    for d in dias:
        factor = _MES_FACTOR[d.month]
        if d.weekday() >= 5:
            factor *= 1.3
        if d.day in _QUINCENA:
            factor *= 1.25
        out.append(max(0.0, nivel_base * factor))
    return out


def _niveles_base(db: Session, comercio_id: int) -> dict[str, float]:
    """Nivel base (promedio diario) por producto desde el histórico de ventas."""
    desde = date.today() - timedelta(days=DIAS_HISTORICO)
    ventas = db.scalars(
        select(VentaRegistro).where(
            VentaRegistro.comercio_id == comercio_id,
            VentaRegistro.fecha >= desde,
        )
    ).all()
    if not ventas:
        return {}
    # Nivel base = promedio de ventas por DÍA DE CALENDARIO (los días sin venta de un
    # producto cuentan como 0), igual que en el entrenamiento (media sobre todos los
    # días). El divisor es el lapso activo del comercio dentro de la ventana.
    primera = min(v.fecha for v in ventas)
    span = (date.today() - primera).days + 1
    span = max(1, min(span, DIAS_HISTORICO))
    suma: dict[str, float] = {}
    for v in ventas:
        suma[v.producto] = suma.get(v.producto, 0.0) + v.cantidad
    return {p: total / span for p, total in suma.items()}


def generar_forecast(db: Session, comercio_id: int) -> dict:
    niveles = _niveles_base(db, comercio_id)
    inventario = {
        i.nombre: i
        for i in db.scalars(
            select(ProductoInventario).where(ProductoInventario.comercio_id == comercio_id)
        ).all()
    }

    productos = sorted(set(niveles) | set(inventario))
    hoy = date.today()
    dias_serie = [hoy + timedelta(days=i) for i in range(1, DIAS_SERIE + 1)]
    dias_prod = dias_serie[:DIAS_PRODUCTO]

    serie_total = [0.0] * DIAS_SERIE
    productos_out = []

    for prod in productos:
        nivel = niveles.get(prod, _nivel_prior())
        serie = _predecir_serie(nivel, dias_serie)
        for idx, val in enumerate(serie):
            serie_total[idx] += val

        demanda_periodo = sum(serie[:DIAS_PRODUCTO])
        inv = inventario.get(prod)
        existencias = float(inv.existencias) if inv else 0.0
        faltante = demanda_periodo - existencias

        # Recomendación de reabasto (cantidad accionable; sin % ambiguo).
        if faltante > 0:
            recomendacion = (
                f"Reabastece: pide ~{math.ceil(faltante)} de {prod} para los próximos "
                f"{DIAS_PRODUCTO} días (tienes {existencias:.0f}, demanda ~{demanda_periodo:.0f})."
            )
        else:
            recomendacion = f"Stock suficiente para {DIAS_PRODUCTO} días."

        # Riesgo de merma: sobrestock y/o caducidad próxima (acumula motivos).
        motivos = []
        if existencias > 0 and existencias > demanda_periodo * 1.5:
            motivos.append("Sobrestock frente a la demanda estimada.")
        if inv and inv.fecha_caducidad and inv.fecha_caducidad <= hoy + timedelta(days=5):
            motivos.append("Caduca pronto: considera una oferta.")
        riesgo = bool(motivos)
        motivo = " ".join(motivos) if motivos else None

        productos_out.append(
            {
                "producto": prod,
                "nivel_base": round(nivel, 2),
                "demanda_estimada": round(demanda_periodo, 1),
                "existencias": existencias,
                "recomendacion_reabasto": recomendacion,
                "riesgo_merma": riesgo,
                "motivo_merma": motivo,
            }
        )

    serie_out = [
        {"fecha": d.isoformat(), "demanda": round(v, 1)}
        for d, v in zip(dias_serie, serie_total)
    ]

    return {
        "comercio_id": comercio_id,
        "periodo": f"próximos {DIAS_PRODUCTO} días",
        "fuente": fuente(),
        "serie_diaria": serie_out,
        "productos": productos_out,
    }
