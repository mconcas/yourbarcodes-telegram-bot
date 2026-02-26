"""Decode barcodes from images using pyzbar."""

from __future__ import annotations

import io
import logging

from PIL import Image
from pyzbar.pyzbar import decode

logger = logging.getLogger(__name__)

# Map pyzbar symbology names → our internal format keys.
_PYZBAR_TO_FORMAT: dict[str, str] = {
    "EAN13": "ean13",
    "EAN8": "ean13",
    "CODE128": "code128",
    "CODE39": "code128",
    "QRCODE": "qrcode",
}


def decode_barcode(image_bytes: bytes) -> list[dict]:
    """Decode all barcodes found in *image_bytes*.

    Each result dict has keys ``data``, ``format``, and ``type_name``.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        results = decode(image)
        decoded: list[dict] = []
        for res in results:
            type_name: str = res.type
            decoded.append({
                "data": res.data.decode("utf-8", errors="replace"),
                "format": _PYZBAR_TO_FORMAT.get(type_name, "code128"),
                "type_name": type_name,
            })
        return decoded
    except Exception:
        logger.exception("Failed to decode barcode")
        return []
