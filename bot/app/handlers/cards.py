"""Card CRUD handlers and the add-card conversation."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.services.barcode_decoder import decode_barcode
from app.services.barcode_generator import (
    SUPPORTED_FORMATS,
    generate_barcode_image,
    validate_code,
)
from app.services.opensearch_client import OpenSearchClient

logger = logging.getLogger(__name__)

# Conversation states
NAME, CODE, FORMAT, CONFIRM = range(4)


def _os(context: ContextTypes.DEFAULT_TYPE) -> OpenSearchClient:
    return context.bot_data["os_client"]


def _owner_id(update: Update) -> int:
    """Return the card owner: user_id in private chats, chat_id in groups."""
    chat = update.effective_chat
    if chat and chat.type != "private":
        return chat.id
    return update.effective_user.id  # type: ignore[union-attr]


# ── format selection keyboard ────────────────────────────────────────
_FORMAT_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton(label, callback_data=f"fmt:{key}")]
    for key, label in SUPPORTED_FORMATS.items()
])


# =====================================================================
#  Add-card conversation
# =====================================================================

async def addcard_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point — ask the user for a card name."""
    _clear_temp(context)
    text = "\u2795 *Add a new card*\n\nType the card name (e.g. \"Supermarket\"):"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")  # type: ignore[union-attr]
    return NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the card name and ask for the code."""
    context.user_data["new_card_name"] = update.message.text.strip()  # type: ignore[union-attr]
    await update.message.reply_text(  # type: ignore[union-attr]
        f"Card name: *{context.user_data['new_card_name']}*\n\n"
        "Now enter the barcode number, or send a photo of the barcode:",
        parse_mode="Markdown",
    )
    return CODE


async def received_code_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User typed the code manually — ask for format."""
    context.user_data["new_card_code"] = update.message.text.strip()  # type: ignore[union-attr]
    await update.message.reply_text(  # type: ignore[union-attr]
        f"Code: `{context.user_data['new_card_code']}`\n\nSelect the barcode format:",
        reply_markup=_FORMAT_KB,
        parse_mode="Markdown",
    )
    return FORMAT


async def received_code_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User sent a photo — decode it, suggest a format, jump to CONFIRM."""
    photo = update.message.photo[-1]  # type: ignore[union-attr]
    tg_file = await photo.get_file()
    image_bytes = await tg_file.download_as_bytearray()

    results = decode_barcode(bytes(image_bytes))
    if not results:
        await update.message.reply_text(  # type: ignore[union-attr]
            "\u274c Could not decode any barcode.\n"
            "Try a clearer photo, or type the code manually."
        )
        return CODE

    result = results[0]
    context.user_data["new_card_code"] = result["data"]
    context.user_data["new_card_format"] = result["format"]
    fmt_label = SUPPORTED_FORMATS.get(result["format"], result["format"])

    await update.message.reply_text(  # type: ignore[union-attr]
        f"\u2705 Decoded: `{result['data']}` ({result['type_name']})\n"
        f"Suggested format: *{fmt_label}*\n\nSave this card?",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("\u2705 Save", callback_data="cfm:yes"),
                InlineKeyboardButton("\U0001f504 Change format", callback_data="cfm:chfmt"),
            ],
            [InlineKeyboardButton("\u274c Cancel", callback_data="cfm:cancel")],
        ]),
        parse_mode="Markdown",
    )
    return CONFIRM


async def received_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User picked a format — validate and ask for confirmation."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    barcode_format = query.data.split(":")[1]  # type: ignore[union-attr]
    code = context.user_data["new_card_code"]

    ok, err = validate_code(code, barcode_format)
    if not ok:
        await query.edit_message_text(f"\u274c {err}\n\nPlease enter a valid code:")
        return CODE

    context.user_data["new_card_format"] = barcode_format
    fmt_label = SUPPORTED_FORMATS[barcode_format]

    await query.edit_message_text(
        "\U0001f4cb *Card summary:*\n\n"
        f"Name: *{context.user_data['new_card_name']}*\n"
        f"Code: `{code}`\n"
        f"Format: *{fmt_label}*\n\n"
        "Save this card?",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("\u2705 Save", callback_data="cfm:yes"),
                InlineKeyboardButton("\u274c Cancel", callback_data="cfm:cancel"),
            ],
        ]),
        parse_mode="Markdown",
    )
    return CONFIRM


async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the final save / cancel / change-format decision."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    action = query.data.split(":")[1]  # type: ignore[union-attr]

    if action == "cancel":
        await query.edit_message_text("\u274c Card creation cancelled.")
        _clear_temp(context)
        return ConversationHandler.END

    if action == "chfmt":
        await query.edit_message_text(
            "Select the barcode format:", reply_markup=_FORMAT_KB
        )
        return FORMAT

    # action == "yes"
    owner = _owner_id(update)
    card_name = context.user_data["new_card_name"]
    card_code = context.user_data["new_card_code"]
    barcode_format = context.user_data["new_card_format"]

    try:
        _os(context).add_card(owner, card_name, card_code, barcode_format)
        await query.edit_message_text(
            f"\u2705 Card *{card_name}* saved!\n\nUse /mycards to view your barcodes.",
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Failed to save card")
        await query.edit_message_text("\u274c Failed to save card. Please try again.")

    _clear_temp(context)
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """``/cancel`` fallback."""
    await update.message.reply_text("\u274c Operation cancelled.")  # type: ignore[union-attr]
    _clear_temp(context)
    return ConversationHandler.END


def _clear_temp(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in ("new_card_name", "new_card_code", "new_card_format"):
        context.user_data.pop(key, None)


# =====================================================================
#  My Cards
# =====================================================================

async def mycards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List saved cards (per-user in private, per-group in groups)."""
    owner = _owner_id(update)
    cards = _os(context).get_cards(owner)

    is_cb = update.callback_query is not None
    if is_cb:
        await update.callback_query.answer()  # type: ignore[union-attr]

    if not cards:
        is_group = update.effective_chat and update.effective_chat.type != "private"
        text = (
            "\U0001f4cb This group doesn\u2019t have any cards yet.\n\nUse /addcard to add one!"
            if is_group
            else "\U0001f4cb You don\u2019t have any cards yet.\n\nUse /addcard to add one!"
        )
        if is_cb:
            await update.callback_query.edit_message_text(text)  # type: ignore[union-attr]
        else:
            await update.message.reply_text(text)  # type: ignore[union-attr]
        return

    rows: list[list[InlineKeyboardButton]] = []
    for card in cards:
        fmt = SUPPORTED_FORMATS.get(card["barcode_format"], card["barcode_format"])
        rows.append([
            InlineKeyboardButton(
                f"\U0001f3f7\ufe0f {card['card_name']} ({fmt})",
                callback_data=f"card:show:{card['id']}",
            )
        ])
    rows.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="menu:back")])

    text = f"\U0001f4cb *Your cards* ({len(cards)}):\n\nTap a card to generate its barcode."
    kb = InlineKeyboardMarkup(rows)
    if is_cb:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")  # type: ignore[union-attr]
    else:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")  # type: ignore[union-attr]


# =====================================================================
#  Show card (generate barcode image on the fly)
# =====================================================================

async def show_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a barcode image for the selected card and send it."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    card_id = query.data.split(":")[2]  # type: ignore[union-attr]
    card = _os(context).get_card(card_id)

    if not card:
        await query.edit_message_text("\u274c Card not found.")
        return
    if card["owner_id"] != _owner_id(update):
        await query.edit_message_text("\u274c This card doesn\u2019t belong to you.")
        return

    try:
        img = generate_barcode_image(card["card_code"], card["barcode_format"])
        fmt_label = SUPPORTED_FORMATS.get(card["barcode_format"], card["barcode_format"])
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,  # type: ignore[union-attr]
            photo=img,
            caption=(
                f"\U0001f3f7\ufe0f *{card['card_name']}*\n"
                f"Code: `{card['card_code']}`\n"
                f"Format: {fmt_label}"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001f4cb My Cards", callback_data="menu:mycards")],
            ]),
        )
    except Exception:
        logger.exception("Barcode generation failed")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,  # type: ignore[union-attr]
            text="\u274c Failed to generate barcode.",
        )


# =====================================================================
#  Delete card
# =====================================================================

async def deletecard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List cards with delete buttons."""
    owner = _owner_id(update)
    cards = _os(context).get_cards(owner)

    if not cards:
        await update.message.reply_text("\U0001f4cb Nothing to delete.")  # type: ignore[union-attr]
        return

    rows = [
        [InlineKeyboardButton(
            f"\U0001f5d1\ufe0f {c['card_name']}",
            callback_data=f"card:del:{c['id']}",
        )]
        for c in cards
    ]
    rows.append([InlineKeyboardButton("\u274c Cancel", callback_data="menu:back")])

    await update.message.reply_text(  # type: ignore[union-attr]
        "\U0001f5d1\ufe0f *Select a card to delete:*",
        reply_markup=InlineKeyboardMarkup(rows),
        parse_mode="Markdown",
    )


async def delete_card_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Actually delete when the button is pressed."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    card_id = query.data.split(":")[2]  # type: ignore[union-attr]
    owner = _owner_id(update)
    card = _os(context).get_card(card_id)

    if card and _os(context).delete_card(card_id, owner):
        await query.edit_message_text(
            f"\u2705 Card *{card['card_name']}* deleted.", parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("\u274c Could not delete card.")


# =====================================================================
#  Build the ConversationHandler
# =====================================================================

def build_addcard_conversation() -> ConversationHandler:
    """Return a ready-to-register ``ConversationHandler``."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("addcard", addcard_entry),
            CallbackQueryHandler(addcard_entry, pattern=r"^menu:addcard$"),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_code_text),
                MessageHandler(filters.PHOTO, received_code_photo),
            ],
            FORMAT: [CallbackQueryHandler(received_format, pattern=r"^fmt:")],
            CONFIRM: [CallbackQueryHandler(confirm_save, pattern=r"^cfm:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True,
        per_chat=True,
    )
