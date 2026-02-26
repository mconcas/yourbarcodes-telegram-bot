"""Start command and top-level menu navigation."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from app.config import WEBAPP_URL


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main-menu inline keyboard."""
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton("\U0001f4cb My Cards", callback_data="menu:mycards")],
        [InlineKeyboardButton("\u2795 Add Card", callback_data="menu:addcard")],
    ]
    # If a WebApp scanner URL is configured, offer a live-scan button.
    if WEBAPP_URL:
        rows.append([
            InlineKeyboardButton(
                "\U0001f4f7 Scan Barcode",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ])
    else:
        rows.append([
            InlineKeyboardButton(
                "\U0001f4f7 Scan Barcode (send photo)",
                callback_data="menu:scan_info",
            )
        ])
    rows.append([
        InlineKeyboardButton("\u2753 Help", callback_data="menu:help"),
    ])
    return InlineKeyboardMarkup(rows)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ``/start`` and ``/help``."""
    text = (
        "\U0001f44b Welcome to *Barcode Bot*!\n\n"
        "I store your loyalty-card barcodes and generate them on the fly.\n\n"
        "Choose an option below:"
    )
    await update.message.reply_text(  # type: ignore[union-attr]
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle generic ``menu:*`` callbacks (help, back, scan_info)."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    action = query.data.split(":")[1]  # type: ignore[union-attr]

    if action == "help":
        await query.edit_message_text(
            "\U0001f4d6 *How to use Barcode Bot:*\n\n"
            "1\ufe0f\u20e3 *Add a card* \u2014 /addcard or tap the menu button\n"
            "2\ufe0f\u20e3 *View cards* \u2014 /mycards to see your saved cards\n"
            "3\ufe0f\u20e3 *Scan a barcode* \u2014 Send me a photo of a barcode\n"
            "4\ufe0f\u20e3 *Get a barcode* \u2014 Tap any card from your list\n"
            "5\ufe0f\u20e3 *Delete a card* \u2014 /deletecard\n\n"
            "Cards are private and tied to your Telegram account.\n"
            "The bot works in private chats and groups.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="menu:back")],
            ]),
            parse_mode="Markdown",
        )
    elif action == "scan_info":
        await query.edit_message_text(
            "\U0001f4f7 *Scan a barcode*\n\n"
            "Send me a photo containing a barcode and I\u2019ll decode it.\n"
            "You can then save it as a card.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="menu:back")],
            ]),
            parse_mode="Markdown",
        )
    elif action == "back":
        await query.edit_message_text(
            "Choose an option:",
            reply_markup=main_menu_keyboard(),
        )
