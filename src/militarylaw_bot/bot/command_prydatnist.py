"""Prydatnist (medical suitability) command on the unified conversation.

Flow: search method → keyword search or group → article → (point) → result.
Every screen is rendered from session.answers, so back navigation can redraw it.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

from telegram import InputMediaPhoto, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, GlobalSession, get_session
from militarylaw_bot.bot.handlers import track_stats
from militarylaw_bot.bot.unified_keyboards import build_grid_keyboard
from militarylaw_bot.bot.utils import get_db_path, get_tables_dir
from militarylaw_bot.domain.suitability import ArticlePoint, SuitabilityDB

logger = logging.getLogger(__name__)

KEYWORD_BUTTON = "🔍 Пошук по ключовому слову"
BROWSE_BUTTON = "📚 Перегляд груп хвороб"
NEXT_BUTTON = "➡️ Далі"
NEW_SEARCH_BUTTON = "🔍 Новий пошук"
ARTICLE_PREFIX = "Стаття "
KEYWORD_PLACEHOLDER = "⌨️ Напишіть назву хвороби"

PRYDATNIST_STATES = (
    "prydatnist_search_method",
    "prydatnist_keyword_input",
    "prydatnist_search_results",
    "prydatnist_groups",
    "prydatnist_articles",
    "prydatnist_article",
    "prydatnist_point",
    "prydatnist_result",
)

_MAX_MESSAGE_LENGTH = 4000  # Telegram limit is 4096

_db: SuitabilityDB | None = None


def _get_db() -> SuitabilityDB:
    global _db
    if _db is None:
        _db = SuitabilityDB(get_db_path())
        logger.info("✅ SuitabilityDB initialized")
    return _db


def _esc(text: str | None) -> str:
    return html.escape(text or "", quote=False)


def _split_message(text: str) -> list[str]:
    """Split text into Telegram-sized chunks on line boundaries."""
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > _MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:_MAX_MESSAGE_LENGTH])
            line = line[_MAX_MESSAGE_LENGTH:]
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > _MAX_MESSAGE_LENGTH:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def _reply(update: Update, text: str, keyboard) -> None:
    """Send HTML text, split if too long; the keyboard goes with the last part."""
    chunks = _split_message(text)
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await update.message.reply_text(
            chunk, parse_mode=ParseMode.HTML, reply_markup=keyboard if is_last else None
        )


def _letter_points(article_number: str) -> list[ArticlePoint]:
    return [p for p in _get_db().get_article_points(article_number) if p.point_letter]


def _find_point(article_number: str, point_letter: str | None) -> ArticlePoint | None:
    points = _get_db().get_article_points(article_number)
    return next(
        (p for p in points if p.point_letter == point_letter), points[0] if points else None
    )


def _point_explanation(article_number: str, point_letter: str):
    """Додаток 2 entry for a point if it has an explanation or tables to show, else None.

    Points with one get their own screen before the conclusion.
    """
    appendix2 = _get_db().get_appendix2_point(article_number, point_letter)
    if appendix2 and (appendix2.details or appendix2.table_number):
        return appendix2
    return None


def _article_title(article_number: str) -> str:
    article = _get_db().get_article(article_number)
    title = f"Стаття {article_number}"
    if article and article.keywords:
        title += f" - {article.keywords}"
    return title


# ===== Screens (built from session.answers) =====
# Each screen returns its text and keyboard. Every text ends with a line telling
# the user what to do next: tap a button or type a message.


def _screen_search_method(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    return texts.PRYDATNIST_INTRO, build_grid_keyboard([KEYWORD_BUTTON, BROWSE_BUTTON], per_row=1)


def _screen_keyword_input(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    return texts.PRYDATNIST_KEYWORD_PROMPT, build_grid_keyboard(
        [], per_row=1, placeholder=KEYWORD_PLACEHOLDER
    )


def _screen_search_results(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    db = _get_db()
    numbers = answers["search_articles"]
    text = (
        f"🔍 <b>За запитом «{_esc(answers['search_keyword'])}» "
        f"знайдено статей: {len(numbers)}</b>\n\n"
    )
    for number in numbers:
        article = db.get_article(number)
        keywords = article.keywords if article else ""
        text += f"<b>Стаття {number}</b> - {_esc(keywords) or 'Без опису'}\n\n"
    text += texts.PRYDATNIST_SEARCH_RESULTS_FOOTER
    labels = [f"{ARTICLE_PREFIX}{n}" for n in numbers]
    return text, build_grid_keyboard(labels, per_row=2)


def _screen_groups(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    groups = _get_db().get_groups()
    text = "📚 <b>Групи хвороб</b>\n\n"
    text += "\n".join(f"<b>{g.roman_numeral}.</b> {_esc(g.title)}" for g in groups)
    text += f"\n\n{texts.PRYDATNIST_CHOOSE_GROUP}"
    return text, build_grid_keyboard([g.roman_numeral for g in groups], per_row=4)


def _screen_articles(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    db = _get_db()
    group = next(g for g in db.get_groups() if g.number == answers["group_number"])
    articles = db.get_articles_by_group(group.number)

    text = f"<b>{group.roman_numeral}. {_esc(group.title)}</b>\n\n"
    if group.details:
        text += f"<i>Пояснення:</i> {_esc(group.details)}\n\n"
    text += f"<b>Статті в групі ({len(articles)}):</b>\n\n"
    for article in articles:
        text += f"<b>Стаття {article.number}</b>\n"
        if article.keywords:
            text += f"Ключові слова: {_esc(article.keywords)}\n"
        text += "\n"
    text += texts.PRYDATNIST_CHOOSE_ARTICLE
    labels = [f"{ARTICLE_PREFIX}{a.number}" for a in articles]
    return text, build_grid_keyboard(labels, per_row=2)


def _screen_article(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    number = answers["article_number"]
    appendix2 = _get_db().get_appendix2_article(number)
    points = _letter_points(number)

    text = f"<b>{_esc(_article_title(number))}</b>\n\n"
    if appendix2 and appendix2.details:
        text += f"<b>Пояснення:</b>\n{_esc(appendix2.details)}\n\n"
    if points:
        text += "<b>Пункти статті:</b>\n"
        for point in points:
            text += f"\n<b>{point.point_letter})</b> {_esc(point.description)}\n"
        text += f"\n{texts.PRYDATNIST_CHOOSE_POINT}"
        if any(_point_explanation(number, p.point_letter) for p in points):
            text += f"\n\n{texts.PRYDATNIST_BROWSE_POINTS_HINT}"
        keyboard = build_grid_keyboard([p.point_letter for p in points], per_row=4)
    else:
        text += texts.PRYDATNIST_CONFIRM_ARTICLE
        keyboard = build_grid_keyboard([NEXT_BUTTON], per_row=1)
    return text, keyboard


def _screen_point(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    number, letter = answers["article_number"], answers["point_letter"]
    point = _find_point(number, letter)
    appendix2 = _get_db().get_appendix2_point(number, letter)

    text = f"<b>Стаття {number}, пункт {letter}</b>\n\n"
    if point and point.description:
        text += f"<b>Опис:</b>\n{_esc(point.description)}\n\n"
    if appendix2 and appendix2.details:
        text += f"<b>Пояснення:</b>\n{_esc(appendix2.details)}\n\n"
    text += texts.PRYDATNIST_CONFIRM_POINT
    return text, build_grid_keyboard([NEXT_BUTTON], per_row=1)


def _screen_result(answers: dict) -> tuple[str, ReplyKeyboardMarkup]:
    number, letter = answers["article_number"], answers.get("point_letter")
    point = _find_point(number, letter)

    source = f"Стаття {number}" + (f", пункт {letter}" if letter else "")
    text = f"🤖 <b>Бот @VijskovePravoBot</b> визначив висновок ({source}):\n\n"
    if point and point.conclusion:
        text += f"<b>{_esc(point.conclusion)}</b>\n"
    else:
        text += "❓ Немає даних для цього діагнозу\n"
    text += f"\n{texts.PRYDATNIST_DISCLAIMER}"
    text += f"\n\n{texts.PRYDATNIST_NEW_SEARCH_HINT}"
    text += texts.CLOSING_NOTE
    return text, build_grid_keyboard([NEW_SEARCH_BUTTON], per_row=1)


_SCREENS = {
    "prydatnist_search_method": _screen_search_method,
    "prydatnist_keyword_input": _screen_keyword_input,
    "prydatnist_search_results": _screen_search_results,
    "prydatnist_groups": _screen_groups,
    "prydatnist_articles": _screen_articles,
    "prydatnist_article": _screen_article,
    "prydatnist_point": _screen_point,
    "prydatnist_result": _screen_result,
}


async def render_prydatnist_step(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: GlobalSession
) -> str:
    """Draw the screen for session.step (used for forward moves and back navigation)."""
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    text, keyboard = _SCREENS[session.step](session.answers)
    await _reply(update, text, keyboard)
    return session.step


async def _send_tables(update: Update, table_numbers: str | None) -> None:
    """Send helper table images for an article as one media group."""
    if not table_numbers:
        return
    tables_dir = Path(get_tables_dir())
    paths = []
    for table_num in (t.strip() for t in table_numbers.split(",")):
        candidates = [tables_dir / f"Таблиця{table_num}.png"]
        if table_num.isdigit():
            candidates.insert(0, tables_dir / f"table-{int(table_num):02d}.jpg")
        found = next((p for p in candidates if p.exists()), None)
        if found:
            paths.append(found)
        else:
            logger.warning(f"Table {table_num} not found in {tables_dir}")
    if not paths:
        return

    files = [open(path, "rb") for path in paths]  # noqa: SIM115 - closed below
    try:
        media = [
            InputMediaPhoto(
                f,
                caption="📋 <b>Допоміжна інформація</b>" if i == 0 else None,
                parse_mode=ParseMode.HTML,
            )
            for i, f in enumerate(files)
        ]
        await update.message.reply_media_group(media)
    except Exception as e:
        logger.error(f"Error sending tables {table_numbers}: {e}")
    finally:
        for f in files:
            f.close()


# ===== Input handling =====


def _typed_article_number(text: str) -> str:
    """Article number from the "Стаття 5" button or from a typed "5"."""
    return text.removeprefix(ARTICLE_PREFIX).strip()


def _latin_roman(text: str) -> str:
    """Roman numeral with Cyrillic look-alikes (Х, І) replaced, so typed and stored forms match."""
    return text.strip().upper().translate(str.maketrans("ХІ", "XI"))


async def start_prydatnist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Enter prydatnist from the main menu, /prydatnist or "new search"."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    session.reset_to_menu()
    session.push_history()  # back from the first screen returns to the main menu
    session.current_command = CommandType.PRYDATNIST
    session.step = "prydatnist_search_method"
    track_stats(chat_id, "prydatnist", "started")
    return await render_prydatnist_step(update, context, session)


async def _move_to(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: GlobalSession,
    step: str,
    **answers,
) -> str:
    """Remember the current screen for back navigation, then show the next one."""
    session.push_history()
    session.answers = {**session.answers, **answers}
    session.step = step
    return await render_prydatnist_step(update, context, session)


async def _invalid_choice(update: Update, session: GlobalSession) -> str:
    """Explain that a button is expected and show the current buttons again."""
    _, keyboard = _SCREENS[session.step](session.answers)
    await update.message.reply_text(
        texts.INVALID_CHOICE, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    return session.step


async def _open_article(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: GlobalSession, number: str
) -> str:
    # Tables go first, so the screen with "what to do next" ends up at the bottom of the chat
    appendix2 = _get_db().get_appendix2_article(number)
    await _send_tables(update, appendix2.table_number if appendix2 else None)
    return await _move_to(
        update, context, session, "prydatnist_article", article_number=number, point_letter=None
    )


async def _on_search_method(update, context, session, text: str) -> str:
    if text == KEYWORD_BUTTON:
        return await _move_to(update, context, session, "prydatnist_keyword_input")
    if text == BROWSE_BUTTON:
        return await _move_to(update, context, session, "prydatnist_groups")
    return await _invalid_choice(update, session)


async def _on_keyword_input(update, context, session, text: str) -> str:
    articles = _get_db().search_by_keyword(text)
    if not articles:
        _, keyboard = _screen_keyword_input(session.answers)
        await update.message.reply_text(
            texts.PRYDATNIST_NOTHING_FOUND.format(keyword=_esc(text)),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        return session.step
    return await _move_to(
        update,
        context,
        session,
        "prydatnist_search_results",
        search_keyword=text,
        search_articles=[a.number for a in articles],
    )


async def _on_search_results(update, context, session, text: str) -> str:
    number = _typed_article_number(text)
    if number in session.answers["search_articles"]:
        return await _open_article(update, context, session, number)
    return await _invalid_choice(update, session)


async def _on_groups(update, context, session, text: str) -> str:
    typed = _latin_roman(text)
    groups = _get_db().get_groups()
    group = next((g for g in groups if _latin_roman(g.roman_numeral) == typed), None)
    if group is None:
        return await _invalid_choice(update, session)
    return await _move_to(
        update, context, session, "prydatnist_articles", group_number=group.number
    )


async def _on_articles(update, context, session, text: str) -> str:
    numbers = [a.number for a in _get_db().get_articles_by_group(session.answers["group_number"])]
    number = _typed_article_number(text)
    if number in numbers:
        return await _open_article(update, context, session, number)
    return await _invalid_choice(update, session)


async def _on_article(update, context, session, text: str) -> str:
    number = session.answers["article_number"]
    points = _letter_points(number)

    if points:
        letter = text.lower().rstrip(")")
        if letter not in [p.point_letter for p in points]:
            return await _invalid_choice(update, session)
        appendix2 = _point_explanation(number, letter)
        if appendix2 is None:
            return await _move_to(
                update, context, session, "prydatnist_result", point_letter=letter
            )
        # Point explanation and tables get their own screen before the result
        await _send_tables(update, appendix2.table_number)
        return await _move_to(update, context, session, "prydatnist_point", point_letter=letter)

    if text == NEXT_BUTTON:
        # The article explanation was already shown on this screen
        return await _move_to(update, context, session, "prydatnist_result", point_letter=None)
    return await _invalid_choice(update, session)


async def _on_point(update, context, session, text: str) -> str:
    if text == NEXT_BUTTON:
        return await _move_to(update, context, session, "prydatnist_result")
    return await _invalid_choice(update, session)


async def _on_result(update, context, session, text: str) -> str:
    if text == NEW_SEARCH_BUTTON:
        return await start_prydatnist(update, context)
    return await _invalid_choice(update, session)


_INPUT_HANDLERS = {
    "prydatnist_search_method": _on_search_method,
    "prydatnist_keyword_input": _on_keyword_input,
    "prydatnist_search_results": _on_search_results,
    "prydatnist_groups": _on_groups,
    "prydatnist_articles": _on_articles,
    "prydatnist_article": _on_article,
    "prydatnist_point": _on_point,
    "prydatnist_result": _on_result,
}


async def handle_prydatnist_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle user input on any prydatnist screen (navigation buttons are handled before)."""
    session = get_session(update.effective_chat.id)
    text = (update.message.text or "").strip()
    return await _INPUT_HANDLERS[session.step](update, context, session, text)


async def handle_legacy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answer taps on inline buttons left in chats by the old prydatnist version."""
    await update.callback_query.answer(
        "Ця кнопка застаріла. Відкрийте «ВЛК» з меню.", show_alert=True
    )
