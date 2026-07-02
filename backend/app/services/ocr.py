"""OCR de tickets (Fase 5, §6 /pantry/scan-ticket).

Motor seleccionable con `OCR_PROVIDER` (settings.ocr_provider):
- "tesseract": OCR local con el binario Tesseract + parser de texto (solo nombres).
- "openai":    visión (OpenAI). El modelo lee el ticket, corrige el OCR y devuelve
               nombre + cantidad + unidad de cada producto.
- "claude":    visión (Anthropic/Claude), ídem.

`escanear_ticket(bytes)` devuelve `(items, texto)`, donde `items` es una lista de
`ProductoOCR`. Si el motor no está disponible/configurado, lanza `OCRNoDisponible`
(el router lo mapea a 503).
"""

import base64
import json
import re

from pydantic import BaseModel

from app.core.config import settings


class OCRNoDisponible(RuntimeError):
    """El motor de OCR no está instalado/configurado en el servidor."""


class ProductoOCR(BaseModel):
    """Un producto detectado en el ticket. cantidad/unidad solo en motores de visión."""

    nombre: str
    cantidad: float | None = None
    unidad: str | None = None  # se trunca a 40 en el router al persistir


class _TicketProductos(BaseModel):
    """Contenedor de salida estructurada para los motores de visión."""

    productos: list[ProductoOCR]


# Líneas de ticket que NO son productos.
_RUIDO = (
    "total", "subtotal", "iva", "cambio", "efectivo", "tarjeta", "gracias",
    "ticket", "caja", "fecha", "hora", "rfc", "folio", "cliente", "importe",
    "propina", "vuelto", "pago", "tel", "suc", "sucursal", "direccion", "www",
)
_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{3,}")

# Instrucción común para los motores de visión (OpenAI/Claude).
_PROMPT_VISION = (
    "Eres un extractor de tickets de compra de supermercado (México). Lee la imagen "
    "del ticket con cuidado y CORRIGE los errores típicos del OCR en los nombres "
    "(abreviaturas, letras/dígitos confundidos). Extrae ÚNICAMENTE los productos "
    "comprados; ignora precios, totales, impuestos y datos de la tienda o del cliente. "
    "Para cada producto devuelve:\n"
    "- nombre: nombre del producto en minúsculas, claro y sin códigos.\n"
    "- cantidad: número de unidades o el peso/volumen si aparece (ej. 2, 0.5, 1.5); "
    "null si no se puede determinar.\n"
    "- unidad: la unidad de esa cantidad (pza, kg, g, l, ml, etc.); null si no aplica.\n"
    'Devuelve JSON con la forma {"productos": [{"nombre": "...", "cantidad": 1, '
    '"unidad": "pza"}, ...]}. Si no hay productos, devuelve {"productos": []}.'
)


def parse_ticket_text(texto: str, max_items: int = 40) -> list[str]:
    """Extrae nombres de producto de un texto OCR de ticket (best-effort)."""
    items: list[str] = []
    vistos: set[str] = set()
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        low = linea.lower()
        if any(r in low for r in _RUIDO):
            continue
        palabras = _PALABRA.findall(linea)
        if not palabras:
            continue
        nombre = " ".join(palabras).strip().lower()
        if len(nombre) < 3 or nombre in vistos:
            continue
        vistos.add(nombre)
        items.append(nombre)
        if len(items) >= max_items:
            break
    return items


def _normalizar(productos: list[ProductoOCR], max_items: int = 40) -> list[ProductoOCR]:
    """Limpia y deduplica los productos devueltos por un motor de visión."""
    items: list[ProductoOCR] = []
    vistos: set[str] = set()
    for p in productos:
        nombre = (p.nombre or "").strip().lower()
        if len(nombre) < 3 or nombre in vistos:
            continue
        vistos.add(nombre)
        cantidad = p.cantidad if (p.cantidad is None or p.cantidad > 0) else None
        unidad = (p.unidad or "").strip().lower() or None
        items.append(ProductoOCR(nombre=nombre, cantidad=cantidad, unidad=unidad))
        if len(items) >= max_items:
            break
    return items


def _detectar_mime(imagen: bytes) -> str:
    """Detecta el media-type por los magic bytes (default JPEG)."""
    if imagen.startswith(b"\x89PNG"):
        return "image/png"
    if imagen[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if imagen[:4] == b"RIFF" and imagen[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _escanear_tesseract(imagen: bytes) -> tuple[list[ProductoOCR], str]:
    """Corre Tesseract sobre la imagen (solo nombres) y devuelve (items, texto_ocr)."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise OCRNoDisponible("Faltan pytesseract/Pillow en el servidor.") from exc

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    import io

    try:
        img = Image.open(io.BytesIO(imagen))
        texto = pytesseract.image_to_string(img, lang="spa+eng")
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRNoDisponible(
            "Tesseract no está instalado. Instálalo o define TESSERACT_CMD."
        ) from exc
    except Exception as exc:  # imagen inválida, etc.
        raise OCRNoDisponible(f"No se pudo procesar la imagen: {exc}") from exc

    items = [ProductoOCR(nombre=n) for n in parse_ticket_text(texto)]
    return items, texto


def _escanear_openai(imagen: bytes) -> tuple[list[ProductoOCR], str]:
    """Extrae nombre/cantidad/unidad del ticket con visión de OpenAI."""
    if not settings.openai_api_key:
        raise OCRNoDisponible(
            "OCR_PROVIDER=openai pero falta OPENAI_API_KEY en el entorno."
        )
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise OCRNoDisponible("Falta el paquete 'openai' en el servidor.") from exc

    mime = _detectar_mime(imagen)
    data_uri = f"data:{mime};base64,{base64.standard_b64encode(imagen).decode()}"
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _PROMPT_VISION},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            response_format=_TicketProductos,
        )
        parsed = resp.choices[0].message.parsed
    except Exception as exc:
        raise OCRNoDisponible(f"Falló el OCR con OpenAI: {exc}") from exc

    if parsed is None:
        raise OCRNoDisponible("OpenAI no devolvió la lista de productos esperada.")
    return _normalizar(parsed.productos), parsed.model_dump_json()


def _escanear_claude(imagen: bytes) -> tuple[list[ProductoOCR], str]:
    """Extrae nombre/cantidad/unidad del ticket con visión de Claude (Anthropic)."""
    if not settings.llm_api_key:
        raise OCRNoDisponible(
            "OCR_PROVIDER=claude pero falta LLM_API_KEY en el entorno."
        )
    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover
        raise OCRNoDisponible("Falta el paquete 'anthropic' en el servidor.") from exc

    mime = _detectar_mime(imagen)
    b64 = base64.standard_b64encode(imagen).decode()
    try:
        client = Anthropic(api_key=settings.llm_api_key)
        resp = client.messages.parse(
            model=settings.llm_model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": _PROMPT_VISION},
                    ],
                }
            ],
            output_format=_TicketProductos,
        )
        parsed = resp.parsed_output
    except Exception as exc:
        raise OCRNoDisponible(f"Falló el OCR con Claude: {exc}") from exc

    if parsed is None:
        raise OCRNoDisponible("Claude no devolvió la lista de productos esperada.")
    return _normalizar(parsed.productos), parsed.model_dump_json()


_MOTORES = {
    "tesseract": _escanear_tesseract,
    "openai": _escanear_openai,
    "claude": _escanear_claude,
}


def escanear_ticket(imagen: bytes) -> tuple[list[ProductoOCR], str]:
    """Despacha al motor de OCR configurado y devuelve (items, texto)."""
    proveedor = (settings.ocr_provider or "tesseract").strip().lower()
    motor = _MOTORES.get(proveedor)
    if motor is None:
        raise OCRNoDisponible(
            f"OCR_PROVIDER='{proveedor}' no válido. Usa: tesseract, openai o claude."
        )
    return motor(imagen)
