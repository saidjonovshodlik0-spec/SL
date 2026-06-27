#!/usr/bin/env python3
"""
📚 Kitoblar bo'yicha ma'lumot beruvchi Telegram Bot
Ishlatish: pip install python-telegram-bot requests
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import requests

# =============================================
# SOZLAMALAR — shu joyni o'zgartiring
# =============================================
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8922682957:AAEMlQgEsBXfo_4MRngkupfdlBHCnf8YCfI")
# =============================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Kitob qidirish (Open Library API) ─────────────────────────────────────────
def search_books(query: str, limit: int = 5) -> list[dict]:
    """Open Library orqali kitob qidiradi (bepul, ro'yxatdan o'tish shart emas)."""
    url = "https://openlibrary.org/search.json"
    params = {"q": query, "limit": limit, "fields": "title,author_name,first_publish_year,isbn,subject,number_of_pages_median"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("docs", [])
        return docs
    except Exception as e:
        logger.error("Qidiruv xatosi: %s", e)
        return []


def format_book(doc: dict, index: int) -> str:
    """Bitta kitob ma'lumotini chiroyli matnga aylantiradi."""
    title = doc.get("title", "Noma'lum")
    authors = ", ".join(doc.get("author_name", ["Noma'lum muallif"]))
    year = doc.get("first_publish_year", "—")
    pages = doc.get("number_of_pages_median", "—")
    subjects = doc.get("subject", [])
    genre = ", ".join(subjects[:3]) if subjects else "—"

    return (
        f"📖 *{index}. {title}*\n"
        f"👤 Muallif: {authors}\n"
        f"📅 Yil: {year}\n"
        f"📄 Sahifalar: {pages}\n"
        f"🏷 Janr: {genre}\n"
    )


# ── /start ─────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🔍 Kitob qidirish", callback_data="help_search")],
        [InlineKeyboardButton("⭐ Mashhur kitoblar", callback_data="popular")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 *Kitoblar bo'yicha ma'lumot beruvchi botga xush kelibsiz!*\n\n"
        "Men sizga kitob haqida quyidagi ma'lumotlarni bera olaman:\n"
        "• Muallif ismi\n"
        "• Nashr yili\n"
        "• Sahifalar soni\n"
        "• Janr / mavzu\n\n"
        "Quyidan tanlang yoki to'g'ridan-to'g'ri kitob nomini yozing 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# ── /help ──────────────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Bot buyruqlari:*\n\n"
        "/start — Bosh menyu\n"
        "/help — Yordam\n"
        "/popular — Mashhur kitoblar\n"
        "/search <nom> — Kitob qidirish\n\n"
        "Yoki shunchaki kitob nomini yoki muallifini yozing!",
        parse_mode="Markdown",
    )


# ── /popular ───────────────────────────────────────────────────────────────────
async def popular_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_popular(update.message)


async def _send_popular(message) -> None:
    await message.reply_text("⏳ Mashhur kitoblar yuklanmoqda...")
    classics = [
        "Harry Potter Rowling",
        "The Great Gatsby Fitzgerald",
        "1984 Orwell",
        "Don Quixote Cervantes",
        "War and Peace Tolstoy",
    ]
    text = "⭐ *Mashhur kitoblardan namunalar:*\n\n"
    for i, q in enumerate(classics, 1):
        docs = search_books(q, limit=1)
        if docs:
            text += format_book(docs[0], i) + "\n"
    await message.reply_text(text, parse_mode="Markdown")


# ── /search <query> ────────────────────────────────────────────────────────────
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text(
            "❗ Iltimos, kitob nomini kiriting.\nMisol: /search Hobbit"
        )
        return
    await _do_search(update.message, query)


# ── Oddiy xabar (kitob nomi yozilganda) ───────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not text:
        return
    await _do_search(update.message, text)


async def _do_search(message, query: str) -> None:
    await message.reply_text(f"🔍 *«{query}»* bo'yicha qidirilmoqda...", parse_mode="Markdown")
    docs = search_books(query, limit=5)
    if not docs:
        await message.reply_text(
            "😔 Kitob topilmadi. Boshqa nom bilan urinib ko'ring."
        )
        return

    result = f"📚 *«{query}»* bo'yicha natijalar ({len(docs)} ta):\n\n"
    for i, doc in enumerate(docs, 1):
        result += format_book(doc, i) + "\n"

    await message.reply_text(result, parse_mode="Markdown")


# ── Inline tugmalar ────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.message.reply_text(
            "🤖 *Bot buyruqlari:*\n\n"
            "/start — Bosh menyu\n"
            "/help — Yordam\n"
            "/popular — Mashhur kitoblar\n"
            "/search <nom> — Kitob qidirish\n\n"
            "Yoki shunchaki kitob nomini yozing!",
            parse_mode="Markdown",
        )
    elif query.data == "popular":
        await _send_popular(query.message)
    elif query.data == "help_search":
        await query.message.reply_text(
            "✍️ Kitob nomini yoki muallif ismini yozing.\n\n"
            "Misol:\n• *Harry Potter*\n• *Tolstoy*\n• *Sherlock Holmes*",
            parse_mode="Markdown",
        )


# ── Asosiy funksiya ────────────────────────────────────────────────────────────
def main() -> None:
    if BOT_TOKEN == "SIZNING_BOT_TOKENINGIZ":
        print("❌ Iltimos, BOT_TOKEN ni o'rnating!")
        print("   @BotFather ga /newbot yuboring va tokenni oling.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("popular", popular_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot ishga tushdi! To'xtatish uchun Ctrl+C bosing.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
