"""Prydatnist (medical suitability) command on the unified conversation.

Flow: search method → keyword search or group → article → (point) → result.
Every screen is rendered from session.answers, so back navigation can redraw it.
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

from telegram import InputMediaPhoto, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, GlobalSession, get_session
from militarylaw_bot.bot.handlers import track_stats
from militarylaw_bot.bot.unified_keyboards import build_grid_keyboard
from militarylaw_bot.bot.utils import get_db_path, get_tables_dir
from militarylaw_bot.domain.suitability import (
    ArticlePoint,
    SuitabilityDB,
    query_terms,
    word_matches_query,
)

logger = logging.getLogger(__name__)

KEYWORD_BUTTON = "🔍 Пошук по ключовому слову"
BROWSE_BUTTON = "📚 Перегляд груп хвороб"
NEXT_BUTTON = "➡️ Далі"
# On a point the search opened directly
OTHER_POINTS_BUTTON = "📄 Інші пункти статті"
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


_WORD = re.compile(r"[\w']+")


def _hl(text: str | None, keyword: str | None) -> str:
    """Escape text and underline the words that match the search query, if there is one."""
    escaped = _esc(text)
    if not keyword:
        return escaped
    terms = query_terms(keyword)
    return _WORD.sub(
        lambda m: f"<u>{m.group(0)}</u>" if word_matches_query(m.group(0), terms) else m.group(0),
        escaped,
    )


def _synonyms_line(keyword: str | None, article_numbers: list[str]) -> str:
    """"Шукали також за схожими словами: …" (those found in the shown articles) or ""."""
    synonyms = _get_db().found_synonyms(keyword, article_numbers) if keyword else []
    if not synonyms:
        return ""
    return texts.PRYDATNIST_SYNONYMS_LINE.format(words=", ".join(_esc(s) for s in synonyms))


def _opened_by_search(answers: dict) -> bool:
    """The search found only this article and opened it, so the user saw no results list."""
    return answers.get("search_articles") == [answers.get("article_number")]


def _jump_letter(answers: dict, number: str) -> str | None:
    """The point to open right away when the article is opened from the search: the one
    point the query singles out, if any. The results list shows it on the button
    ("Стаття 20, пункт а"), so the user knows where the button leads.
    """
    keyword = answers.get("search_keyword")
    if not keyword:
        return None
    letters = _get_db().best_points(keyword, number)
    return letters[0] if len(letters) == 1 else None


def _points_label(letters: list[str]) -> tuple[str, str]:
    """("пункт а", "в пункті а") or ("пункти а, б", "в пунктах а, б")."""
    joined = ", ".join(letters)
    if len(letters) == 1:
        return f"пункт {joined}", f"в пункті {joined}"
    return f"пункти {joined}", f"в пунктах {joined}"


def _quoted_words(words: list[str]) -> dict[str, str]:
    """{"words": "«астми», «астматичного»", "verb": "згадуються"} for the mention hints."""
    shown = words[:3]
    return {
        "words": ", ".join(f"«{_esc(w)}»" for w in shown),
        "verb": "згадується" if len(shown) == 1 else "згадуються",
    }


def _search_hint(keyword: str, number: str, in_results: bool) -> str:
    """Where the query was found in the article, or "" if it does not single out points."""
    db = _get_db()
    letters = db.best_points(keyword, number)
    if not letters:
        # The query does not tell the points apart (all match, or the article has one point),
        # or it is only in the explanation of the whole article (e.g. "раку" in article 54).
        # Say where it is only if the article is not about this disease.
        if db.article_names_disease(keyword, number):
            return ""
        template = (
            texts.PRYDATNIST_RESULTS_MENTION_HINT if in_results
            else texts.PRYDATNIST_SEARCH_MENTION_HINT
        )
        point_letters = [p.point_letter for p in _letter_points(number)]
        with_words = [
            letter for letter in point_letters if db.mentioned_words(keyword, number, [letter])
        ]
        if with_words:
            words = db.mentioned_words(keyword, number, with_words)
            return template.format(**_quoted_words(words), where=_points_label(with_words)[1])
        words = db.explanation_mentioned_words(keyword, number)
        if not words:
            return ""
        return template.format(**_quoted_words(words), where="в поясненні до статті")
    points, where = _points_label(letters)
    if db.article_names_disease(keyword, number):
        template = (
            texts.PRYDATNIST_RESULTS_POINTS_HINT if in_results
            else texts.PRYDATNIST_SEARCH_POINTS_HINT
        )
        return template.format(keyword=_esc(keyword), points=points)
    # The article is not about this disease: say exactly which word was found there
    with_words = [letter for letter in letters if db.mentioned_words(keyword, number, [letter])]
    words = db.mentioned_words(keyword, number, with_words)
    if words:
        _, where = _points_label(with_words)
        template = (
            texts.PRYDATNIST_RESULTS_MENTION_HINT if in_results
            else texts.PRYDATNIST_SEARCH_MENTION_HINT
        )
        return template.format(**_quoted_words(words), where=where)
    template = (
        texts.PRYDATNIST_RESULTS_PARTIAL_HINT if in_results
        else texts.PRYDATNIST_SEARCH_PARTIAL_HINT
    )
    return template.format(where=where)


_HTML_TAG = re.compile(r"<(/?)(b|i|u|s|a|code|pre)\b[^>]*>")


def _balance_tags(chunks: list[str]) -> list[str]:
    """Close tags left open at the end of a chunk and reopen them in the next one.

    Telegram rejects a message with an unclosed tag, so a split inside <i>…</i>
    would drop that part of the screen together with its keyboard.
    """
    balanced = []
    carried: list[str] = []  # opening tags still open from previous chunks
    for chunk in chunks:
        text = "".join(carried) + chunk
        stack = list(carried)
        for match in _HTML_TAG.finditer(chunk):
            if match.group(1):
                if stack:
                    stack.pop()
            else:
                stack.append(match.group(0))
        closing = "".join(f"</{_HTML_TAG.match(tag).group(2)}>" for tag in reversed(stack))
        balanced.append(text + closing)
        carried = stack
    return balanced


def _pack(pieces: list[str], separator: str) -> list[str]:
    """Join pieces with separator into chunks no longer than the message limit."""
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}{separator}{piece}" if current else piece
        if current and len(candidate) > _MAX_MESSAGE_LENGTH:
            chunks.append(current)
            current = piece
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _split_message(text: str) -> list[str]:
    """Split text into Telegram-sized chunks, keeping HTML tags balanced.

    Splits between paragraphs where possible, so a block like the closing
    "what to do next" prompt stays in one message; falls back to lines,
    then to a hard cut for a single overlong line.
    """
    pieces: list[str] = []
    for paragraph in _pack(text.split("\n\n"), "\n\n"):
        if len(paragraph) <= _MAX_MESSAGE_LENGTH:
            pieces.append(paragraph)
            continue
        for block in _pack(paragraph.split("\n"), "\n"):
            pieces.extend(
                block[i:i + _MAX_MESSAGE_LENGTH] for i in range(0, len(block), _MAX_MESSAGE_LENGTH)
            )
    return _balance_tags(pieces)


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
        f"знайдено статей: {len(numbers)}</b>\n"
    )
    synonyms = _synonyms_line(answers["search_keyword"], numbers)
    if synonyms:
        text += synonyms + "\n"
    text += "\n"
    keyword = answers["search_keyword"]
    for number in numbers:
        article = db.get_article(number)
        keywords = article.keywords if article else ""
        text += f"<b>Стаття {number}</b> - {_hl(keywords, keyword) or 'Без опису'}\n"
        hint = _search_hint(keyword, number, in_results=True)
        if hint:
            text += hint + "\n"
        text += "\n"
    text += texts.PRYDATNIST_SEARCH_RESULTS_FOOTER
    # A button says the point too when it opens that point right away
    labels = []
    for number in numbers:
        letter = _jump_letter(answers, number)
        labels.append(f"{ARTICLE_PREFIX}{number}" + (f", пункт {letter}" if letter else ""))
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

    keyword = answers.get("search_keyword")
    text = f"<b>{_hl(_article_title(number), keyword)}</b>\n\n"
    if keyword and _opened_by_search(answers):
        synonyms = _synonyms_line(keyword, [number])
        if synonyms:
            text += synonyms + "\n\n"
    if appendix2 and appendix2.details:
        text += f"<b>Пояснення:</b>\n{_hl(appendix2.details, keyword)}\n\n"
    if points:
        text += "<b>Пункти статті:</b>\n"
        for point in points:
            text += f"\n<b>{point.point_letter})</b> {_hl(point.description, keyword)}\n"
        hint = _search_hint(keyword, number, in_results=False) if keyword else ""
        if hint:
            text += f"\n{hint}\n"
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

    text = ""
    if answers.get("search_hit") == letter:
        # Opened straight from the search: say why this point was chosen
        keyword = answers["search_keyword"]
        db = _get_db()
        words = [] if db.article_names_disease(keyword, number) else (
            db.mentioned_words(keyword, number, [letter])
        )
        if words:
            # The article is not about this disease, it is only mentioned in the point
            text += texts.PRYDATNIST_SEARCH_HIT_MENTION.format(
                **_quoted_words(words), article=number, letter=letter
            ) + "\n"
        else:
            text += texts.PRYDATNIST_SEARCH_HIT.format(
                keyword=_esc(keyword), article=number, letter=letter
            ) + "\n"
        if _opened_by_search(answers):
            synonyms = _synonyms_line(answers["search_keyword"], [number])
            if synonyms:
                text += synonyms + "\n"
        text += "\n"
    text += f"<b>Стаття {number}, пункт {letter}</b>\n\n"
    keyword = answers.get("search_keyword")
    if point and point.description:
        text += f"<b>Опис:</b>\n{_hl(point.description, keyword)}\n\n"
    if appendix2 and appendix2.details:
        text += f"<b>Пояснення:</b>\n{_hl(appendix2.details, keyword)}\n\n"
        question = texts.PRYDATNIST_CONFIRM_POINT_QUESTION
    else:
        question = texts.PRYDATNIST_CONFIRM_DESCRIPTION_QUESTION

    if answers.get("search_hit") != letter:
        text += question + texts.PRYDATNIST_CONFIRM_POINT_ANSWERS
        return text, build_grid_keyboard([NEXT_BUTTON], per_row=1)
    # Opened straight from the search, so the article screen was skipped: offer it as a button.
    # "Назад" returns to the screen the user came from (the results list or the query).
    back_to = (
        "щоб повернутися до результатів пошуку" if len(answers.get("search_articles") or []) > 1
        else "щоб змінити запит"
    )
    text += question + texts.PRYDATNIST_CONFIRM_SEARCH_HIT_ANSWERS.format(back_to=back_to)
    return text, build_grid_keyboard([NEXT_BUTTON, OTHER_POINTS_BUTTON], per_row=1)


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
    """Article number from a "Стаття 5" / "Стаття 5, пункт б" button or from a typed "5"."""
    return text.removeprefix(ARTICLE_PREFIX).split(",")[0].strip()


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
    _advance(session, step, **answers)
    return await render_prydatnist_step(update, context, session)


def _advance(session: GlobalSession, step: str, **answers) -> None:
    """Remember the current screen for back navigation and switch to step without showing it."""
    session.push_history()
    session.answers = {**session.answers, **answers}
    session.step = step


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
    """Show the article; if the search query points to one point, go straight to it.

    The point screen still asks whether the explanation fits and offers the other points
    of the article and the other search results.
    """
    # Tables go first, so the screen with "what to do next" ends up at the bottom of the chat
    db = _get_db()
    appendix2 = db.get_appendix2_article(number)
    await _send_tables(update, appendix2.table_number if appendix2 else None)

    letter = _jump_letter(session.answers, number)
    if letter is None:
        return await _move_to(
            update, context, session, "prydatnist_article", article_number=number, point_letter=None
        )
    # The article screen is skipped and not put into history: "Назад" from the point goes
    # back to what the user actually saw before it
    point_appendix2 = db.get_appendix2_point(number, letter)
    await _send_tables(update, point_appendix2.table_number if point_appendix2 else None)
    return await _move_to(
        update, context, session, "prydatnist_point",
        article_number=number, point_letter=letter, search_hit=letter,
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
    found = {"search_keyword": text, "search_articles": [a.number for a in articles]}
    if len(articles) == 1:
        # Nothing to choose from: skip the results list and open the article
        session.answers = {**session.answers, **found}
        return await _open_article(update, context, session, articles[0].number)

    return await _move_to(update, context, session, "prydatnist_search_results", **found)


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
    if text == OTHER_POINTS_BUTTON and session.answers.get("search_hit"):
        # A step forward to the article; "Назад" from there returns to this point
        return await _move_to(
            update, context, session, "prydatnist_article", point_letter=None, search_hit=None
        )
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
