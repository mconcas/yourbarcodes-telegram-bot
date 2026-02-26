"""Handlers for barcode scanning — photo decoding + WebApp scan-to-save flow."""

from __future__ import annotations

import json
import logging

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.services.barcode_decoder import decode_barcode
from app.services.barcode_generator import SUPPORTED_FORMATS
from app.services.opensearch_client import OpenSearchClient

logger = logging.getLogger(__name__)

# State for the webapp-scan conversation
SCAN_CARD_NAME = 0

_FMT_MAP = {
    "QR_CODE": "qrcode",
    "QRCODE": "qrcode",
    "EAN_13": "ean13",
    "EAN_8": "ean13",
    "CODE_128": "code128",
    "CODE_39": "code128",
}


def _os(context: ContextTypes.DEFAULT_TYPE) -> OpenSearchClient:
    return context.bot_data["os_client"]


# =====================================================================
#  Photo handler (standalone, outside any conversation)
# =====================================================================

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


# =====================================================================
#  WebApp scan → ask name → save card  (dedicated ConversationHandler)
# =====================================================================

async def _webapp_scan_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: receive barcode data from the WebApp, ask for a card name."""
    logger.info("WebApp scan data received from user %s", update.effective_user.id)

    data = update.effective_message.web_app_data.data  # type: ignore[union-attr]
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid JSON from webapp: %s", data)
        await update.message.reply_text("\u274c Invalid data from scanner.")  # type: ignore[union-attr]
        return ConversationHandler.END

    code = payload.get("code", "")
    fmt_raw = payload.get("format", "")
    barcode_format = _FMT_MAP.get(fmt_raw, "code128")
    fmt_label = SUPPORTED_FORMATS.get(barcode_format, barcode_format)

    context.user_data["scan_card_code"] = code
    context.user_data["scan_card_format"] = barcode_format

    await update.message.reply_text(  # type: ignore[union-attr]
        f"\U0001f4f7 *Scanned barcode*\n\n"
        f"Code: `{code}`\n"
        f"Format: {fmt_label}\n\n"
        "\u270f\ufe0f Type a name for this card (e.g. \"Supermarket\"):",
        parse_mode="Markdown",
    )
    return SCAN_CARD_NAME


async def _webapp_received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed a card name — save it straight away."""
    card_name = update.message.text.strip()  # type: ignore[union-attr]
    card_code = context.user_data.pop("scan_card_code", "")
    barcode_format = context.user_data.pop("scan_card_format", "code128")
    user_id = update.effective_user.id  # type: ignore[union-attr]
    fmt_label = SUPPORTED_FORMATS.get(barcode_format, barcode_format)

    try:
        _os(context).add_card(user_id, card_name, card_code, barcode_format)
        await update.message.reply_text(  # type: ignore[union-attr]
            f"\u2705 Card *{card_name}* saved!\n\n"
            f"Code: `{card_code}`\n"
            f"Format: {fmt_label}\n\n"
            "Use /mycards to view your barcodes.",
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Failed to save card from webapp scan")
        await update.message.reply_text(  # type: ignore[union-attr]
            "\u274c Failed to save card. Please try again."
        )
    return ConversationHandler.END


async def _webapp_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the webapp-scan card creation."""
    context.user_data.pop("scan_card_code", None)
    context.user_data.pop("scan_card_format", None)
    await update.message.reply_text("\u274c Cancelled.")  # type: ignore[union-attr]
    return ConversationHandler.END


def build_webapp_scan_conversation() -> ConversationHandler:
    """Return a ConversationHandler for the webapp-scan → name → save flow."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.StatusUpdate.WEB_APP_DATA, _webapp_scan_entry),
        ],
        states={
            SCAN_CARD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _webapp_received_name),
            ],
        },
        fallbacks=[CommandHandler("cancel", _webapp_cancel)],
        per_user=True,
        per_chat=True,
    )
