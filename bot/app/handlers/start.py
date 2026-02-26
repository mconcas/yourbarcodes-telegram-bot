"""Start command and top-level menu navigation."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import ContextTypes

from app.config import WEBAPP_URL


def main_menu_keyboard(
    *, is_private: bool = True, bot_username: str = "", chat_id: int = 0,
) -> InlineKeyboardMarkup:
    """Build the main-menu inline keyboard.

    In groups, swaps the scanner row for a deep-link to the private chat
    because Telegram only supports webapp buttons in private chats.
    """
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton("\U0001f4cb My Cards", callback_data="menu:mycards")],
        [InlineKeyboardButton("\u2795 Add Card", callback_data="menu:addcard")],
    ]
    if WEBAPP_URL and not is_private and bot_username:
        rows.append([
            InlineKeyboardButton(
                "\U0001f4f7 Scan Barcode",
                url=f"https://t.me/{bot_username}?start=scan_{chat_id}",
            )
        ])
    elif not WEBAPP_URL:
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


def scanner_reply_keyboard() -> ReplyKeyboardMarkup | None:
    """Build a persistent reply keyboard with the webapp scanner button.

    ``sendData()`` only works when the Mini App is opened from a
    ``KeyboardButton``, so we use the reply keyboard for the scanner.
    """
    if not WEBAPP_URL:
        return None
    return ReplyKeyboardMarkup(
        [[KeyboardButton("\U0001f4f7 Scan Barcode", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ``/start`` and ``/help``."""
    is_private = update.effective_chat.type == "private"  # type: ignore[union-attr]
    bot_username = context.bot.username or ""

    # Deep-link: /start scan  or  /start scan_<group_chat_id>
    if is_private and context.args and context.args[0].startswith("scan"):
        payload = context.args[0]  # "scan" or "scan_-1001234567890"
        if "_" in payload:
            try:
                group_chat_id = int(payload.split("_", 1)[1])
                context.user_data["scan_target_chat"] = group_chat_id
            except (ValueError, IndexError):
                pass  # Ignore malformed deep-link; fall back to private
        reply_kb = scanner_reply_keyboard()
        if reply_kb:
            await update.message.reply_text(  # type: ignore[union-attr]
                "\U0001f4f7 Tap the *Scan Barcode* button below to open the scanner:",
                reply_markup=reply_kb,
                parse_mode="Markdown",
            )
            return

    text = (
        "\U0001f44b Welcome to *Barcode Bot*!\n\n"
        "I store your loyalty-card barcodes and generate them on the fly.\n\n"
        "Choose an option below:"
    )
    # Send the inline menu
    await update.message.reply_text(  # type: ignore[union-attr]
        text,
        reply_markup=main_menu_keyboard(
            is_private=is_private,
            bot_username=bot_username,
            chat_id=update.effective_chat.id,  # type: ignore[union-attr]
        ),
        parse_mode="Markdown",
    )
    # In private chats, also set the persistent reply keyboard with the scanner
    if is_private:
        reply_kb = scanner_reply_keyboard()
        if reply_kb:
            await update.message.reply_text(  # type: ignore[union-attr]
                "\u2b07\ufe0f Use the button below to scan barcodes anytime:",
                reply_markup=reply_kb,
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
        is_private = update.effective_chat.type == "private"  # type: ignore[union-attr]
        bot_username = context.bot.username or ""
        await query.edit_message_text(
            "Choose an option:",
            reply_markup=main_menu_keyboard(
                is_private=is_private,
                bot_username=bot_username,
                chat_id=update.effective_chat.id,  # type: ignore[union-attr]
            ),
        )
