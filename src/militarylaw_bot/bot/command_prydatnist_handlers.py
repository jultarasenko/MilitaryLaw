"""Unified handlers for /prydatnist command using global session."""

from __future__ import annotations

import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.unified_keyboards import (
    prydatnist_search_method,
    result_actions,
)
from militarylaw_bot.domain.suitability import SuitabilityDB
from militarylaw_bot.bot.utils import get_db_path

logger = logging.getLogger(__name__)

_suitability_db = None


def _init_db():
    """Initialize database on first use."""
    global _suitability_db
    if _suitability_db is None:
        try:
            db_path = get_db_path()
            _suitability_db = SuitabilityDB(db_path)
            logger.info(f"✅ SuitabilityDB initialized: {db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SuitabilityDB: {e}")


async def handle_prydatnist_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle /prydatnist command - show search method selection."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    # Reset to prydatnist command
    session.current_command = CommandType.PRYDATNIST
    session.answers.clear()
    session.step = "prydatnist_search_method"

    _init_db()

    text = (
        "🏥 <b>Оцінка придатності до військової служби</b>\n\n"
        "Виберіть спосіб пошуку хвороби:\n\n"
        "<i>Рекомендація: якщо у вас кілька хвороб, краще пройтись по кожній окремо.</i>"
    )

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        text,
        reply_markup=prydatnist_search_method(),
        parse_mode="HTML",
    )

    return "prydatnist_search_method"


async def handle_prydatnist_search_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle search method selection."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "🔍 Пошук по ключовому слову":
        session.answers["search_method"] = "keyword"
        session.push_history()
        session.step = "prydatnist_keyword_input"

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            "🔍 <b>Введіть ключове слово хвороби</b>\n\nНаприклад: туберкульоз",
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "prydatnist_keyword_input"

    elif text == "📚 Перегляд груп хвороб":
        session.answers["search_method"] = "browse"
        session.push_history()
        session.step = "prydatnist_groups"

        _init_db()
        groups = _suitability_db.get_groups() if _suitability_db else []

        text_msg = "📚 <b>Групи хвороб</b>\n\n"
        for i, group in enumerate(groups, 1):
            text_msg += f"{i}. {group.name}\n"

        from militarylaw_bot.bot.unified_keyboards import prydatnist_groups_navigation
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            text_msg,
            reply_markup=prydatnist_groups_navigation(len(groups)),
            parse_mode="HTML",
        )
        return "prydatnist_groups"

    else:
        await update.message.reply_text("❌ Виберіть один з варіантів")
        return "prydatnist_search_method"


async def handle_prydatnist_keyword_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle keyword search input."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    keyword = update.message.text.strip()

    _init_db()

    if not _suitability_db:
        await update.message.reply_text("❌ Помилка: база даних не ініціалізована")
        return "prydatnist_keyword_input"

    # Search articles by keyword
    articles = _suitability_db.search_by_keyword(keyword)

    if not articles:
        await update.message.reply_text(
            f"❌ <b>Не знайдено статей для: \"{keyword}\"</b>\n\n"
            "Спробуйте повторити пошук по іншому ключовому слову.",
            parse_mode="HTML",
        )
        return "prydatnist_keyword_input"

    session.answers["search_results"] = articles
    session.answers["search_keyword"] = keyword
    session.step = "prydatnist_result"

    # Show results
    result_text = f"📋 <b>Результати пошуку для: \"{keyword}\"</b>\n\n"
    for article in articles:
        result_text += f"Стаття {article.number}\n"

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        result_text,
        reply_markup=result_actions(),
        parse_mode="HTML",
    )

    return "prydatnist_result"


async def handle_prydatnist_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle disease groups browsing."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    _init_db()

    if not _suitability_db:
        await update.message.reply_text("❌ Помилка: база даних не ініціалізована")
        return "prydatnist_groups"

    groups = _suitability_db.get_groups()

    # Try to parse as group number
    if not text.isdigit():
        await update.message.reply_text("❌ Виберіть номер групи")
        return "prydatnist_groups"

    group_num = int(text)
    if group_num < 1 or group_num > len(groups):
        await update.message.reply_text(f"❌ Група повинна бути від 1 до {len(groups)}")
        return "prydatnist_groups"

    group = groups[group_num - 1]
    session.answers["selected_group"] = group_num
    session.answers["group_id"] = group.id
    session.push_history()
    session.step = "prydatnist_articles"

    # Get articles in group
    articles = _suitability_db.get_articles_by_group(group.id)
    session.answers["group_articles"] = [a.number for a in articles]

    text_msg = f"📚 <b>Група: {group.name}</b>\n\n"
    text_msg += f"Статей в групі: {len(articles)}\n\n"
    text_msg += "Виберіть номер статті"

    from militarylaw_bot.bot.unified_keyboards import prydatnist_articles_navigation
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        text_msg,
        reply_markup=prydatnist_articles_navigation(len(articles)),
        parse_mode="HTML",
    )
    return "prydatnist_articles"


async def handle_prydatnist_articles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle article selection within group."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    _init_db()

    if not _suitability_db:
        await update.message.reply_text("❌ Помилка: база даних не ініціалізована")
        return "prydatnist_articles"

    articles = session.answers.get("group_articles", [])

    if not text.isdigit():
        await update.message.reply_text("❌ Виберіть номер статті")
        return "prydatnist_articles"

    article_idx = int(text)
    if article_idx < 1 or article_idx > len(articles):
        await update.message.reply_text(f"❌ Стаття повинна бути від 1 до {len(articles)}")
        return "prydatnist_articles"

    article_num = articles[article_idx - 1]
    session.answers["selected_article"] = article_num
    session.push_history()
    session.step = "prydatnist_points"

    # Get points for article
    article = _suitability_db.get_article(article_num)
    if not article or not article.points:
        session.step = "prydatnist_result"
        text_msg = f"📋 <b>Стаття {article_num}</b>\n\nНема розділів для цієї статті"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            text_msg,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "prydatnist_result"

    text_msg = f"📋 <b>Стаття {article_num}</b>\n\n"
    text_msg += f"Розділів: {len(article.points)}\n\n"
    text_msg += "Виберіть розділ (букву)"

    from militarylaw_bot.bot.unified_keyboards import prydatnist_points_navigation
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        text_msg,
        reply_markup=prydatnist_points_navigation(len(article.points)),
        parse_mode="HTML",
    )
    return "prydatnist_points"


async def handle_prydatnist_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle point selection for article."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip().upper()

    _init_db()

    if not _suitability_db:
        await update.message.reply_text("❌ Помилка: база даних не ініціалізована")
        return "prydatnist_points"

    article_num = session.answers.get("selected_article")
    article = _suitability_db.get_article(article_num)

    if not article or not article.points:
        await update.message.reply_text("❌ Стаття не знайдена")
        return "prydatnist_points"

    # Convert letter to index (A=0, B=1, etc.)
    if len(text) != 1 or ord(text) < ord('A') or ord(text) > ord('Z'):
        await update.message.reply_text("❌ Виберіть букву від A до Z")
        return "prydatnist_points"

    point_idx = ord(text) - ord('A')
    if point_idx >= len(article.points):
        await update.message.reply_text(f"❌ Розділ повинен бути від A до {chr(ord('A') + len(article.points) - 1)}")
        return "prydatnist_points"

    point = article.points[point_idx]
    session.answers["selected_point"] = point.letter
    session.push_history()
    session.step = "prydatnist_result"

    # Build result message
    text_msg = f"📋 <b>Стаття {article_num} розділ {point.letter}</b>\n\n"
    text_msg += point.description or "Без опису"

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        text_msg,
        reply_markup=result_actions(),
        parse_mode="HTML",
    )
    return "prydatnist_result"


async def handle_prydatnist_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle result screen navigation."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    if text == "🔍 Нов пошук":
        session.answers.clear()
        session.step = "prydatnist_search_method"
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            "🏥 <b>Оцінка придатності до військової служби</b>\n\n"
            "Виберіть спосіб пошуку хвороби:",
            reply_markup=prydatnist_search_method(),
            parse_mode="HTML",
        )
        return "prydatnist_search_method"

    return "prydatnist_result"
