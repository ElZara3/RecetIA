"""OCR de tickets (Fase 5, §6 /pantry/scan-ticket) con Tesseract.

`escanear_ticket(bytes)` corre Tesseract sobre la imagen y devuelve (items, texto).
El parser (`parse_ticket_text`) es una función pura, fácil de probar sin el binario.
"""

import re

from app.core.config import settings


class OCRNoDisponible(RuntimeError):
    """Tesseract no está instalado/configurado en el servidor."""


# Líneas de ticket que NO son productos.
_RUIDO = (
    "total", "subtotal", "iva", "cambio", "efectivo", "tarjeta", "gracias",
    "ticket", "caja", "fecha", "hora", "rfc", "folio", "cliente", "importe",
    "propina", "vuelto", "pago", "tel", "suc", "sucursal", "direccion", "www",
)
_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{3,}")


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


def escanear_ticket(imagen: bytes) -> tuple[list[str], str]:
    """Corre Tesseract sobre la imagen y devuelve (items, texto_ocr)."""
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

    return parse_ticket_text(texto), texto
