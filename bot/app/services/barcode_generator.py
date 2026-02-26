"""Generate barcode / QR-code images in memory."""

from __future__ import annotations

import io

import barcode
from barcode.writer import ImageWriter
import qrcode

# Formats the bot supports.  Keys are stored in OpenSearch.
SUPPORTED_FORMATS: dict[str, str] = {
    "ean13": "EAN-13",
    "code128": "Code 128",
    "qrcode": "QR Code",
}


def generate_barcode_image(code: str, barcode_format: str) -> io.BytesIO:
    """Return a PNG image of the barcode as a seeked-to-zero BytesIO."""
    buf = io.BytesIO()

    if barcode_format == "qrcode":
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buf, format="PNG")
    else:
        bc_class = barcode.get_barcode_class(barcode_format)
        writer = ImageWriter()
        bc = bc_class(code, writer=writer)
        bc.write(buf, options={
            "module_width": 0.4,
            "module_height": 20.0,
            "font_size": 14,
            "text_distance": 5.0,
            "quiet_zone": 6.5,
            "dpi": 300,
        })

    buf.seek(0)
    return buf


def validate_code(code: str, barcode_format: str) -> tuple[bool, str]:
    """Check that *code* is valid for *barcode_format*.

    Returns ``(ok, error_message)``.
    """
    if not code:
        return False, "Code cannot be empty."

    if barcode_format == "ean13":
        if not code.isdigit():
            return False, "EAN-13 codes must contain only digits."
        if len(code) not in (12, 13):
            return False, "EAN-13 codes must be 12 or 13 digits long."
    elif barcode_format == "code128":
        pass  # Code 128 accepts any ASCII string
    elif barcode_format == "qrcode":
        pass  # QR codes accept arbitrary data
    else:
        return False, f"Unknown format: {barcode_format}"

    return True, ""
