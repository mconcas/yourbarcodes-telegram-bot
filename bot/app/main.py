"""Barcode Bot — entry point."""

from __future__ import annotations

import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import LOG_LEVEL, OPENSEARCH_HOST, OPENSEARCH_PORT, TELEGRAM_BOT_TOKEN
from app.handlers.cards import (
    build_addcard_conversation,
    delete_card_cb,
    deletecard_command,
    mycards,
    show_card,
)
from app.handlers.scan import handle_photo
from app.handlers.start import menu_callback, start_command
from app.services.opensearch_client import OpenSearchClient


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s  %(name)-30s  %(levelname)-7s  %(message)s",
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    )
    logger = logging.getLogger(__name__)

    # ── OpenSearch ────────────────────────────────────────────────────
    os_client = OpenSearchClient(OPENSEARCH_HOST, OPENSEARCH_PORT)
    os_client.wait_for_cluster()
    os_client.init_index()
    logger.info("OpenSearch ready")

    # ── Telegram application ──────────────────────────────────────────
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.bot_data["os_client"] = os_client

    # 1. Conversation handler for /addcard  (must be first so it can
    #    intercept menu:addcard callbacks and text messages while active)
    app.add_handler(build_addcard_conversation())

    # 2. Slash commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("mycards", mycards))
    app.add_handler(CommandHandler("deletecard", deletecard_command))

    # 3. Callback-query handlers (more-specific patterns first)
    app.add_handler(CallbackQueryHandler(mycards, pattern=r"^menu:mycards$"))
    app.add_handler(CallbackQueryHandler(show_card, pattern=r"^card:show:"))
    app.add_handler(CallbackQueryHandler(delete_card_cb, pattern=r"^card:del:"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"))

    # 4. Standalone photo handler (scan outside the add-card flow)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Starting polling …")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
