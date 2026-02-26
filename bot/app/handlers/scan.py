"""Handlers for barcode photo scanning (outside the add-card conversation)."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.services.barcode_decoder import decode_barcode
from app.services.barcode_generator import SUPPORTED_FORMATS

logger = logging.getLogger(__name__)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Decode barcodes from an incoming photo.

    In group chats the bot stays silent when nothing is found so it
    doesn't spam the conversation.
    """
    is_private = update.effective_chat.type == "private"  # type: ignore[union-attr]

    photo = update.message.photo[-1]  # type: ignore[union-attr]
    tg_file = await photo.get_file()
    image_bytes = await tg_file.download_as_bytearray()

    results = decode_barcode(bytes(image_bytes))

    if not results:
        if is_private:
            await update.message.reply_text(  # type: ignore[union-attr]
                "\u274c Could not decode any barcode from this photo.\n"
                "Try a clearer photo with good lighting."
            )
        return

    for i, res in enumerate(results):
        fmt_label = SUPPORTED_FORMATS.get(res["format"], res["format"])
        await update.message.reply_text(  # type: ignore[union-attr]
            f"\u2705 *Decoded barcode"
            + (f" #{i + 1}" if len(results) > 1 else "")
            + f"*\n\n"
            f"Data: `{res['data']}`\n"
            f"Type: {res['type_name']}\n"
            f"Suggested format: {fmt_label}\n\n"
            "To save it, use /addcard and paste the code\n"
            "(or send the same photo during that flow).",
            parse_mode="Markdown",
        )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process data returned by the Telegram WebApp barcode scanner.

    The webapp sends JSON ``{"code": "...", "format": "..."}``.
    """
    import json

    data = update.effective_message.web_app_data.data  # type: ignore[union-attr]
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        await update.message.reply_text("\u274c Invalid data from scanner.")  # type: ignore[union-attr]
        return

    code = payload.get("code", "")
    fmt_raw = payload.get("format", "")
    # Normalise the JS format name
    fmt_map = {"QR_CODE": "qrcode", "EAN_13": "ean13", "CODE_128": "code128"}
    barcode_format = fmt_map.get(fmt_raw, "code128")
    fmt_label = SUPPORTED_FORMATS.get(barcode_format, barcode_format)

    await update.message.reply_text(  # type: ignore[union-attr]
        f"\U0001f4f7 *Scanned via camera*\n\n"
        f"Data: `{code}`\n"
        f"Format: {fmt_label}\n\n"
        "Use /addcard to save this code.",
        parse_mode="Markdown",
    )
