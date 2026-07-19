"""Implementation of /prydatnist (medical suitability assessment) command."""

from __future__ import annotations

import logging
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from militarylaw_bot.domain.suitability import SuitabilityDB
from militarylaw_bot.bot.utils import get_db_path, get_tables_dir
from militarylaw_bot.bot.message_tracker import MessageTracker
from militarylaw_bot.bot import texts

logger = logging.getLogger(__name__)

# Initialize database
_suitability_db = None
_tables_dir = None
_message_tracker = None

COMMAND_NAME = "prydatnist"

# Context keys for tracking state
CONTEXT_KEY_ARTICLE = "pryd_article_number"
CONTEXT_KEY_POINT = "pryd_point_letter"
CONTEXT_KEY_SELECTED_UNITS = "pryd_selected_units"  # list of (column_number, name)


def _get_state(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get prydatnist state from context."""
    if "prydatnist_state" not in context.user_data:
        context.user_data["prydatnist_state"] = {
            "article_number": None,
            "point_letter": None,
            "selected_units": [],  # [(column_number, name), ...]
            "history": [],  # Stack of (step_name, step_data) for back button
        }
    return context.user_data["prydatnist_state"]


def _reset_state(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Reset prydatnist state (new session)."""
    context.user_data["prydatnist_state"] = {
        "article_number": None,
        "point_letter": None,
        "selected_units": [],
        "history": [],
    }
    return context.user_data["prydatnist_state"]


def _push_history(state: dict, step_name: str, step_data: dict = None) -> None:
    """Push current step to history for back button."""
    if "history" not in state:
        state["history"] = []
    state["history"].append({
        "step": step_name,
        "data": step_data or {}
    })
    logger.info(f"📍 PUSH history: {step_name}, total: {len(state['history'])}")


def _pop_history(state: dict) -> dict | None:
    """Pop previous step from history."""
    if "history" not in state:
        state["history"] = []
    if not state["history"]:
        logger.info("📍 POP history: EMPTY")
        return None
    popped = state["history"].pop()
    logger.info(f"📍 POP history: {popped['step']}, remaining: {len(state['history'])}")
    return popped


def _init_tracker():
    """Initialize message tracker on first use."""
    global _message_tracker
    if _message_tracker is None:
        try:
            tracker_path = get_db_path("message_tracker.db")
            _message_tracker = MessageTracker(tracker_path)
            logger.info(f"✅ MessageTracker initialized: {tracker_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MessageTracker: {e}")


def _init_db():
    """Initialize database on first use."""
    global _suitability_db, _tables_dir
    if _suitability_db is None:
        try:
            db_path = get_db_path()
            _suitability_db = SuitabilityDB(db_path)
            logger.info(f"✅ SuitabilityDB initialized: {db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SuitabilityDB: {e}")

    if _tables_dir is None:
        _tables_dir = get_tables_dir()
        logger.info(f"Tables directory: {_tables_dir}")


async def _safe_delete_message(chat_id: int, message_id: int, bot_instance, user_id: int = None) -> bool:
    """Safely delete a message, returning True if successful. Skip if saved."""
    # Don't delete saved messages
    if user_id:
        _init_tracker()
        if _message_tracker and _message_tracker.is_saved(user_id, message_id):
            logger.debug(f"Skipping deletion of saved message {message_id}")
            return False

    try:
        await bot_instance.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"🗑 Deleted prydatnist message {message_id}")
        return True
    except Exception as e:
        logger.debug(f"Could not delete prydatnist message {message_id}: {e}")
        return False


async def _send_pryd(
    query,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    context: ContextTypes.DEFAULT_TYPE | None = None,
) -> None:
    """Edit message and manage message history. Split if text exceeds 4096 chars."""
    # Telegram limit is 4096 characters
    MAX_LENGTH = 4090

    if len(text) > MAX_LENGTH:
        # Split into parts - find last newline to avoid breaking mid-sentence
        logger.warning(f"Text too long ({len(text)} chars), truncating...")
        truncated = text[:MAX_LENGTH]
        # Try to cut at last newline
        last_newline = truncated.rfind('\n')
        if last_newline > MAX_LENGTH - 500:  # If newline is relatively close
            text = truncated[:last_newline] + "\n\n[...]"
        else:
            # Just truncate and close any open tags
            text = truncated + "\n\n[...]"

    try:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return

    # Track message using MessageTracker (command-specific)
    _init_tracker()
    if _message_tracker and context:
        try:
            user_id = query.from_user.id
            chat_id = query.message.chat_id
            message_id = query.message.message_id

            # Delete helper messages (tables) from previous step
            helper_msg_ids = _message_tracker.get_helper_messages(user_id, COMMAND_NAME)
            for helper_msg_id in helper_msg_ids:
                await _safe_delete_message(chat_id, helper_msg_id, context.bot, user_id)
            if helper_msg_ids:
                _message_tracker.clear_helper_messages(user_id, COMMAND_NAME)

            # Get previous message for this command
            prev_record = _message_tracker.get_last_message(user_id, COMMAND_NAME)

            # Delete previous message if it's different from current
            if prev_record and prev_record.message_id != message_id:
                await _safe_delete_message(chat_id, prev_record.message_id, context.bot, user_id)

            # Store current message
            _message_tracker.set_last_message(user_id, COMMAND_NAME, chat_id, message_id)
        except Exception as e:
            logger.error(f"Error tracking message: {e}")


async def handle_prydatnist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prydatnist command - start medical suitability assessment."""
    if not update.message:
        return

    target = update.message
    chat_id = target.chat_id
    user_id = update.effective_user.id

    logger.info(f"User {chat_id} started /prydatnist")

    # Reset state for new session
    _reset_state(context)

    _init_db()
    _init_tracker()

    if not _suitability_db:
        logger.error("SuitabilityDB is None!")
        await target.reply_text("❌ Помилка: база даних не ініціалізована")
        return

    text = (
        "🏥 <b>Оцінка придатності до військової служби</b>\n\n"
        "Виберіть спосіб пошуку хвороби:\n\n"
        "<i>Рекомендація: якщо у вас кілька хвороб, краще пройтись по кожній окремо.</i>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Пошук по ключовому слову", callback_data="pryd_search_keyword")],
        [InlineKeyboardButton("📚 Перегляд груп хвороб", callback_data="pryd_browse_groups")],
    ])

    msg = await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    # Track message using MessageTracker
    if _message_tracker:
        prev_record = _message_tracker.get_last_message(user_id, COMMAND_NAME)
        if prev_record:
            await _safe_delete_message(chat_id, prev_record.message_id, context.bot, user_id)
        _message_tracker.set_last_message(user_id, COMMAND_NAME, chat_id, msg.message_id)

    logger.info(f"✅ Sent /prydatnist intro to {chat_id}")


async def handle_prydatnist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route /prydatnist callbacks (filtered by pattern r'^pryd_')."""
    query = update.callback_query
    data = query.data

    logger.info(f"Prydatnist callback: {data}")

    _init_db()
    _init_tracker()

    if not _suitability_db:
        logger.error("SuitabilityDB is None in handle_prydatnist_callback!")
        await query.answer("❌ Помилка: база даних не ініціалізована", show_alert=True)
        return

    try:
        if data == "pryd_search_keyword":
            logger.info("[ROUTE] -> _handle_search_keyword")
            await _handle_search_keyword(query, _suitability_db, context)
        elif data == "pryd_browse_groups":
            logger.info("[ROUTE] -> _handle_browse_groups")
            await _handle_browse_groups(query, _suitability_db, context)
        elif data == "pryd_back_to_start":
            await _render_main_menu(query, context)
        elif data == "pryd_save_result":
            logger.info("[ROUTE] -> _handle_save_result")
            await _handle_save_result(query, context)
        elif data.startswith("pryd_group_"):
            logger.info("[ROUTE] -> _handle_group_select")
            await _handle_group_select(query, _suitability_db, data, context)
        elif data.startswith("pryd_article_"):
            logger.info("[ROUTE] -> _handle_article_select")
            try:
                await _handle_article_select(query, _suitability_db, data, context)
            except Exception as e:
                logger.error(f"❌ ERROR in _handle_article_select: {e}", exc_info=True)
        elif data.startswith("pryd_point_"):
            logger.info("[ROUTE] -> _handle_point_select")
            await _handle_point_select(query, _suitability_db, data, context)
        elif data.startswith("pryd_unit_toggle_"):
            logger.info("[ROUTE] -> _handle_unit_toggle")
            await _handle_unit_toggle(query, _suitability_db, data, context)
        elif data == "pryd_show_units":
            state = _get_state(context)
            article_number = state.get("article_number")
            point_letter = state.get("point_letter")

            # Check if there are requirements for this article/point
            has_requirements = _suitability_db.has_requirements(article_number, point_letter)

            if has_requirements:
                logger.info("[ROUTE] -> _send_unit_selection")
                await _send_unit_selection(query, _suitability_db, context)
            else:
                logger.info("[ROUTE] -> _handle_show_results_no_requirements (no requirements, skip unit selection)")
                await _handle_show_results_no_requirements(query, _suitability_db, context)
        elif data == "pryd_unit_next":
            logger.info("[ROUTE] -> _handle_show_results")
            await _handle_show_results(query, _suitability_db, context)
        elif data == "pryd_go_home":
            logger.info("[ROUTE] -> go home (back to prydatnist menu)")
            await _render_main_menu(query, context)
        elif data == "pryd_start_new":
            logger.info("[ROUTE] -> start new (save result and restart)")
            # Save the message (so it won't be deleted)
            _init_tracker()
            if _message_tracker:
                user_id = query.from_user.id
                message_id = query.message.message_id
                _message_tracker.save_message(user_id, message_id)

                from militarylaw_bot.bot.session import get_session
                session = get_session(context)
                if message_id not in session.saved_message_ids:
                    session.saved_message_ids.append(message_id)

                logger.info(f"✅ Saved prydatnist result {message_id} for user {user_id}")

            # Remove buttons from saved message
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass

            # Clear state for new session
            _reset_state(context)

            # Send NEW message (not edit current)
            user_id = query.from_user.id
            chat_id = query.message.chat_id
            text = (
                "🏥 <b>Оцінка придатності до військової служби</b>\n\n"
                "Виберіть спосіб пошуку хвороби:\n\n"
                "<i>Рекомендація: якщо у вас кілька хвороб, краще пройтись по кожній окремо.</i>"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Пошук по ключовому слову", callback_data="pryd_search_keyword")],
                [InlineKeyboardButton("📚 Перегляд груп хвороб", callback_data="pryd_browse_groups")],
            ])
            msg = await query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

            # Track new message
            if _message_tracker:
                _message_tracker.set_last_message(user_id, COMMAND_NAME, chat_id, msg.message_id)
        elif data == "pryd_go_back":
            state = _get_state(context)
            prev_step = _pop_history(state)

            if not prev_step:
                # No history, go to main menu
                await _render_main_menu(query, context)
                return

            step_name = prev_step["step"]
            step_data = prev_step.get("data", {})
            logger.info(f"🔙 Going back to step: {step_name}, data: {step_data}")

            if step_name == "main_menu":
                # Back to main menu
                await _render_main_menu(query, context)
            elif step_name == "search_keyword":
                # Back to search keyword prompt
                state["_returning_from_back"] = True
                await _handle_search_keyword(query, _suitability_db, context)
            elif step_name == "groups":
                # Back to groups list
                await _handle_browse_groups(query, _suitability_db, context)
            elif step_name == "articles":
                # Back to articles list - render group with articles WITHOUT pushing history again
                group_number = step_data.get("group_number")
                if group_number:
                    await _render_articles_for_group(query, _suitability_db, group_number, context)
                else:
                    # If group not saved, go back to browse groups
                    await _handle_browse_groups(query, _suitability_db, context)
            elif step_name == "article_details":
                # Back to article details
                article_number = step_data.get("article_number")
                if article_number:
                    state["_returning_from_back"] = True
                    await _handle_article_select(
                        query,
                        _suitability_db,
                        f"pryd_article_{article_number}",
                        context
                    )
                else:
                    await _render_main_menu(query, context)
            elif step_name == "unit_selection":
                # Back to unit selection (points)
                article_number = step_data.get("article_number")
                point_letter = step_data.get("point_letter")
                if article_number and point_letter:
                    state["_returning_from_back"] = True
                    await _handle_point_select(
                        query,
                        _suitability_db,
                        f"pryd_point_{article_number}_{point_letter}",
                        context
                    )
                else:
                    await _render_main_menu(query, context)
            else:
                # Unknown step, go to main menu
                await _render_main_menu(query, context)
        elif data.startswith("pryd_unit_"):
            logger.info("[ROUTE] -> _handle_unit_select (legacy)")
            await _handle_unit_select(query, _suitability_db, data, context)
        else:
            logger.warning(f"Unknown callback: {data}")
            await query.answer("Невідома команда")
    except Exception as e:
        logger.error(f"Error handling callback {data}: {e}", exc_info=True)
        await query.answer(f"❌ Помилка: {str(e)[:50]}", show_alert=True)


# ===== Callback handlers =====

async def _handle_save_result(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save result message so it won't be deleted by /start."""
    _init_tracker()
    if not _message_tracker:
        await query.answer("❌ Помилка: не вдалося зберегти")
        return

    user_id = query.from_user.id
    message_id = query.message.message_id

    # Save in message tracker
    _message_tracker.save_message(user_id, message_id)

    # Also save in session (for consistency with vidstrochka)
    from militarylaw_bot.bot.session import get_session
    session = get_session(context)
    if message_id not in session.saved_message_ids:
        session.saved_message_ids.append(message_id)

    # Remove buttons from message
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    await query.answer("✅ Результат збережено!")
    logger.info(f"✅ Saved prydatnist result {message_id} for user {user_id}")


async def _render_main_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Render main menu (used for back button)."""
    logger.info("🔵 _render_main_menu called")
    text = (
        "🏥 <b>Оцінка придатності до військової служби</b>\n\n"
        "Виберіть спосіб пошуку хвороби:\n\n"
        "<i>Рекомендація: якщо у вас кілька хвороб, краще пройтись по кожній окремо.</i>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Пошук по ключовому слову", callback_data="pryd_search_keyword")],
        [InlineKeyboardButton("📚 Перегляд груп хвороб", callback_data="pryd_browse_groups")],
    ])

    try:
        await _send_pryd(query, text, keyboard, context)
        logger.info("🟢 _render_main_menu success")
    except Exception as e:
        logger.error(f"🔴 _render_main_menu error: {e}", exc_info=True)


async def _handle_search_keyword(query, db, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt for disease keyword search."""
    state = _get_state(context)

    # Push to history if not returning from back
    if not state.get("_returning_from_back"):
        _push_history(state, "search_keyword")
    state["_returning_from_back"] = False

    state["search_mode"] = True

    text = "🔍 <b>Введіть ключове слово хвороби</b>\n\nНаприклад: туберкульоз"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")],
    ])
    await _send_pryd(query, text, keyboard, context)


async def handle_keyword_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for keyword search."""
    if not update.message or not update.message.text:
        return

    # Only process if in search mode
    state = _get_state(context)
    if not state.get("search_mode"):
        return

    state["search_mode"] = False  # Reset search mode

    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    keyword = update.message.text.strip()

    _init_db()
    _init_tracker()

    logger.info(f"🔍 Keyword search for: {keyword}")

    # Remove buttons from the search prompt message
    try:
        prev_record = _message_tracker.get_last_message(user_id, COMMAND_NAME) if _message_tracker else None
        if prev_record:
            await context.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=prev_record.message_id,
                reply_markup=None
            )
            logger.info(f"Removed buttons from search prompt message {prev_record.message_id}")
    except Exception as e:
        logger.debug(f"Could not remove buttons from search prompt: {e}")

    # Search articles, groups, and point descriptions
    articles = _suitability_db.search_by_keyword(keyword)

    if not articles:
        text = f"❌ <b>Не знайдено статей для: \"{keyword}\"</b>\n\nСпробуйте повторити пошук по іншому ключовому слову або виберіть інший спосіб пошуку."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Новий пошук", callback_data="pryd_search_keyword")],
            [InlineKeyboardButton("📚 Перегляд груп хвороб", callback_data="pryd_browse_groups")],
        ])
        msg = await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

        # Track message
        if _message_tracker:
            _message_tracker.set_last_message(user_id, COMMAND_NAME, chat_id, msg.message_id)
        return

    # Show search results
    text = f"🔍 <b>Результати пошуку для \"{keyword}\":</b>\n\n"
    keyboard_buttons = []

    for article in articles:
        text += f"<b>Стаття {article.number}</b> - {article.keywords}\n"
        callback = f"pryd_article_{article.number}"
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"Стаття {article.number}",
                callback_data=callback
            )
        ])

    keyboard_buttons.append([InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    msg = await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    # Track message
    if _message_tracker:
        _message_tracker.set_last_message(user_id, COMMAND_NAME, chat_id, msg.message_id)

    logger.info(f"Found {len(articles)} articles for keyword: {keyword}")


async def _handle_browse_groups(query, db, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show groups of diseases."""
    # Don't push - this is the first step after main menu

    groups = db.get_groups()

    text = "📚 <b>Групи хвороб</b>\n\n"
    keyboard_buttons = []

    for group in groups:
        text += f"{group.roman_numeral}. {group.title}\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{group.roman_numeral}. {group.title[:30]}...",
                callback_data=f"pryd_group_{group.number}"
            )
        ])

    keyboard_buttons.append([InlineKeyboardButton("↩ Назад", callback_data="pryd_back_to_start")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await _send_pryd(query, text, keyboard, context)


async def _render_articles_for_group(query, db, group_number: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Render articles for group without modifying history."""
    state = _get_state(context)

    groups = db.get_groups()
    group = next((g for g in groups if g.number == group_number), None)

    if not group:
        await query.answer("Групу не знайдено")
        return

    articles = db.get_articles_by_group(group_number)

    text = f"<b>{group.roman_numeral}. {group.title}</b>\n\n"
    if group.details:
        text += f"<i>Пояснення:</i> {group.details}\n\n"
    text += f"<b>Статті в групі ({len(articles)}):</b>\n\n"

    for article in articles:
        text += f"<b>Стаття {article.number}</b>\n"
        if article.keywords:
            text += f"Ключові слова: {article.keywords}\n"
        text += "\n"

    keyboard_buttons = []
    for article in articles:
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{article.number}",
                callback_data=f"pryd_article_{article.number}"
            )
        ])

    keyboard_buttons.append([InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await _send_pryd(query, text, keyboard, context)

    # Mark next interaction as "returning from back" so article selection won't re-push history
    state["_returning_from_back"] = True


async def _handle_group_select(query, db, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show articles in selected group."""
    state = _get_state(context)
    group_number = int(data.split("_")[-1])

    # Only push to history if not returning from back
    if not state.get("_returning_from_back"):
        _push_history(state, "groups", {"group_number": group_number})
    state["_returning_from_back"] = False

    groups = db.get_groups()
    group = next((g for g in groups if g.number == group_number), None)

    if not group:
        await query.answer("Групу не знайдено")
        return

    articles = db.get_articles_by_group(group_number)

    text = f"<b>{group.roman_numeral}. {group.title}</b>\n\n"
    if group.details:
        text += f"<i>Пояснення:</i> {group.details}\n\n"
    text += f"<b>Статті в групі ({len(articles)}):</b>\n\n"

    # List articles with keywords
    for article in articles:
        text += f"<b>Стаття {article.number}</b>\n"
        if article.keywords:
            text += f"Ключові слова: {article.keywords}\n"
        text += "\n"

    keyboard_buttons = []
    for article in articles:
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{article.number}",
                callback_data=f"pryd_article_{article.number}"
            )
        ])

    keyboard_buttons.append([InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")])
    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await _send_pryd(query, text, keyboard, context)


async def _handle_article_select(query, db, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show details for selected article."""
    state = _get_state(context)
    article_number = data.split("_")[-1]
    logger.info(f"📄 Article select: {article_number}, _returning_from_back={state.get('_returning_from_back')}")

    article = db.get_article(article_number)
    all_points = db.get_article_points(article_number)
    # Filter to only points with non-empty point_letter
    points = [p for p in all_points if p.point_letter]
    appendix2_article = db.get_appendix2_article(article_number)

    # Only push to history if not returning from back
    if not state.get("_returning_from_back"):
        group_number = article.group_number if article else None
        _push_history(state, "articles", {"article_number": article_number, "group_number": group_number})
    state["_returning_from_back"] = False

    text = f"<b>Стаття {article_number}"
    if article and article.keywords:
        text += f" - {article.keywords}"
    text += "</b>\n\n"

    if appendix2_article and appendix2_article.details:
        details = appendix2_article.details.replace("<", "&lt;").replace(">", "&gt;")
        text += f"<b>Пояснення:</b>\n{details}\n\n"

    logger.info(f"📍 Article {article_number} has {len(points)} points: {[p.point_letter for p in points]}")

    keyboard_buttons = []

    # Only show points section if there are points with letters
    if points:
        text += "<b>Пункти:</b>\n"
        for point in points:
            desc = point.description.replace("<", "&lt;").replace(">", "&gt;") if point.description else ""
            text += f"\n<b>{point.point_letter})</b> {desc}\n"

        for point in points:
            callback = f"pryd_point_{article_number}_{point.point_letter}"
            logger.info(f"📍 Creating button for point {point.point_letter}: callback={callback}")
            keyboard_buttons.append([
                InlineKeyboardButton(
                    f"{point.point_letter}",
                    callback_data=callback
                )
            ])

    # If no points, add "Далі" button to go to military units selection
    if not points:
        state = _get_state(context)
        state["article_number"] = article_number
        state["point_letter"] = None
        state["selected_units"] = []

        # Always show "Back" and "Next" buttons for articles without points
        keyboard_buttons.append([
            InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back"),
            InlineKeyboardButton("➡️ Далі", callback_data="pryd_show_units"),
        ])
    else:
        keyboard_buttons.append([InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")])

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    await _send_pryd(query, text, keyboard, context)

    # Send table if exists
    if appendix2_article and appendix2_article.table_number:
        user_id = query.from_user.id
        await _send_tables(query.message, appendix2_article.table_number, context, user_id)


async def _handle_point_select(query, db, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show military units for selection (multiple choice)."""
    parts = data.split("_")
    article_number = parts[2]
    point_letter = parts[3] if len(parts) > 3 else None
    if point_letter == "none":
        point_letter = None

    logger.info(f"📍 Point select: article={article_number}, point={point_letter}, data={data}")

    # Save to state
    state = _get_state(context)

    # Only push to history if not returning from go_back
    if not state.get("_returning_from_back"):
        _push_history(state, "article_details", {
            "article_number": article_number,
            "point_letter": point_letter
        })
    state["_returning_from_back"] = False

    state["article_number"] = article_number
    state["point_letter"] = point_letter
    state["selected_units"] = []  # Reset selection

    # Get point info
    points = db.get_article_points(article_number)
    point = next((p for p in points if p.point_letter == point_letter), None)

    # Check if has appendix2 details (pояснення)
    has_appendix2_details = False
    if point_letter:
        appendix2_point = db.get_appendix2_point(article_number, point_letter)
        has_appendix2_details = appendix2_point and appendix2_point.details
    else:
        appendix2_article = db.get_appendix2_article(article_number)
        has_appendix2_details = appendix2_article and appendix2_article.details

    # Check if has requirements in appendix3
    has_requirements = db.has_requirements(article_number, point_letter)

    # If no appendix2 details, skip directly to next step
    if not has_appendix2_details:
        logger.info(f"No appendix2 details for article {article_number} point {point_letter}, skipping to next step")
        if has_requirements:
            # Skip explanation, go directly to unit selection
            await _send_unit_selection(query, db, context)
        else:
            # Skip explanation and unit selection, go directly to results
            await _handle_show_results_no_requirements(query, db, context)
        return

    # Show explanation message
    text = f"<b>Стаття {article_number}"
    if point_letter:
        text += f", пункт {point_letter}</b>\n\n"
    else:
        text += "</b>\n\n"

    if point:
        # Escape HTML in description and conclusion
        desc = point.description.replace("<", "&lt;").replace(">", "&gt;") if point.description else ""
        text += f"<b>Опис:</b>\n{desc}\n\n"

    # Get appendix2 point details
    if point_letter:
        appendix2_point = db.get_appendix2_point(article_number, point_letter)
        if appendix2_point and appendix2_point.details:
            details = appendix2_point.details.replace("<", "&lt;").replace(">", "&gt;")
            text += f"<b>Пояснення:</b>\n{details}\n\n"
    else:
        appendix2_article = db.get_appendix2_article(article_number)
        if appendix2_article and appendix2_article.details:
            details = appendix2_article.details.replace("<", "&lt;").replace(">", "&gt;")
            text += f"<b>Пояснення:</b>\n{details}\n\n"

    if has_requirements:
        # Message: Point details with Back and Next buttons
        keyboard_buttons = [
            InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back"),
            InlineKeyboardButton("➡️ Далі", callback_data="pryd_show_units"),
        ]
        keyboard = InlineKeyboardMarkup([keyboard_buttons])

        # Edit current message (replace it with point details)
        await _send_pryd(query, text, keyboard, context)
    else:
        # No requirements - show conclusion directly
        text = "🤖 Бот @VijskovePravoBot визначив висновок:\n\n"
        if point and point.conclusion:
            text += f"<b>{point.conclusion}</b>"
        else:
            text += "❓ Немає даних для цього діагнозу\n"

        text += texts.CLOSING_NOTE

        keyboard_buttons = [
            [InlineKeyboardButton("💾 Зберегти й почати спочатку", callback_data="pryd_start_new")],
            [InlineKeyboardButton("🏠 Повернутись на стартову сторінку", callback_data="pryd_go_home")],
            [InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")],
        ]

        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        await _send_pryd(query, text, keyboard, context)


async def _send_unit_selection(query, db, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show military units selection (edit current message)."""
    state = _get_state(context)
    units = db.get_military_units()

    text = f"<b>Виберіть військові спеціалізації (можна кілька):</b>\n\n"

    # List units in text
    for unit in units:
        text += f"<b>{unit.column_number}</b>. {unit.name}\n"

    # Build keyboard with unit toggle buttons
    keyboard_buttons = []
    selected_ids = [u[0] for u in state.get("selected_units", [])]

    for unit in units:
        mark = "✅" if unit.column_number in selected_ids else "⭕"
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{mark} {unit.column_number}",
                callback_data=f"pryd_unit_toggle_{unit.column_number}"
            )
        ])

    # Add "Back" and "Next" buttons (Back on left, Next on right)
    keyboard_buttons.append([
        InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back"),
        InlineKeyboardButton("➡️ Далі", callback_data="pryd_unit_next"),
    ])

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    # Edit current message (replace point details with unit selection)
    await _send_pryd(query, text, keyboard, context)


async def _handle_unit_toggle(query, db, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle selection of a military unit."""
    column_number = int(data.split("_")[-1])
    state = _get_state(context)

    # Find unit
    unit = next(
        (u for u in db.get_military_units() if u.column_number == column_number),
        None
    )

    if not unit:
        await query.answer("Спеціалізацію не знайдено")
        return

    # Toggle selection
    selected_ids = [u[0] for u in state["selected_units"]]
    if column_number in selected_ids:
        state["selected_units"] = [(u[0], u[1]) for u in state["selected_units"] if u[0] != column_number]
        await query.answer(f"✖️ {unit.name} видалена")
    else:
        state["selected_units"].append((column_number, unit.name))
        await query.answer(f"✅ {unit.name} вибрана")

    # Redraw the unit selection message
    units = db.get_military_units()
    text = f"<b>Виберіть військові спеціалізації (можна кілька):</b>\n\n"
    selected_ids = [u[0] for u in state["selected_units"]]

    for unit in units:
        mark = "✅" if unit.column_number in selected_ids else "❌"
        text += f"{mark} <b>{unit.column_number}</b>. {unit.name}\n"

    keyboard_buttons = []
    for unit in units:
        mark = "✅" if unit.column_number in selected_ids else "⭕"
        keyboard_buttons.append([
            InlineKeyboardButton(
                f"{mark} {unit.column_number}",
                callback_data=f"pryd_unit_toggle_{unit.column_number}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back"),
        InlineKeyboardButton("➡️ Далі", callback_data="pryd_unit_next"),
    ])

    keyboard = InlineKeyboardMarkup(keyboard_buttons)

    # Edit the unit selection message (not the point details message above)
    try:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        logger.info(f"✏️ Updated unit selection message {query.message.message_id}")
    except Exception as e:
        logger.error(f"Error updating unit selection: {e}")


async def _handle_show_results(query, db, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show results for all selected units."""
    state = _get_state(context)

    if not state["selected_units"]:
        await query.answer("Виберіть хоча б одну спеціалізацію")
        return

    article_number = state["article_number"]
    point_letter = state["point_letter"]

    # Push unit selection to history
    _push_history(state, "unit_selection", {
        "article_number": article_number,
        "point_letter": point_letter
    })

    # Get point conclusion
    points = db.get_article_points(article_number)
    point = next(
        (p for p in points if p.point_letter == point_letter),
        points[0] if points else None
    )

    # Build result text
    text = "🤖 <b>Бот @VijskovePravoBot</b> визначив придатність до наступних військових спеціалізацій:\n\n"

    for column_number, unit_name in state["selected_units"]:
        requirements = db.get_requirements(
            article_number,
            point_letter,
            [column_number]
        )

        if requirements:
            req = requirements[0]
            if req.requirement == "НП":
                text += f"❌ <b>{unit_name}</b> - Непридатний\n"
            else:
                text += f"✅ <b>{unit_name}</b> - Придатний ({req.requirement})\n"
        else:
            # Use conclusion from article_points
            if point and point.conclusion:
                text += f"📋 <b>{unit_name}</b>\n{point.conclusion}\n"
            else:
                text += f"❓ <b>{unit_name}</b> - Немає даних\n"

    text += texts.CLOSING_NOTE

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Зберегти й почати спочатку", callback_data="pryd_start_new")],
        [InlineKeyboardButton("🏠 Повернутись на стартову сторінку", callback_data="pryd_go_home")],
        [InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")],
    ])

    # Edit current message to show results (replace unit selection)
    await _send_pryd(query, text, keyboard, context)


async def _handle_show_results_no_requirements(query, db, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show results when article/point has no requirements (no unit selection needed)."""
    state = _get_state(context)

    article_number = state["article_number"]
    point_letter = state["point_letter"]

    # Push a placeholder for unit_selection in history
    _push_history(state, "unit_selection", {
        "article_number": article_number,
        "point_letter": point_letter
    })

    # Get point conclusion
    points = db.get_article_points(article_number)
    point = next(
        (p for p in points if p.point_letter == point_letter),
        points[0] if points else None
    )

    # Get article if no point
    if not point:
        article = db.get_article(article_number)
        if article:
            point_text = f"Стаття {article_number}"
            if article.keywords:
                point_text += f" - {article.keywords}"
        else:
            point_text = f"Стаття {article_number}"
    else:
        if point_letter:
            point_text = f"Стаття {article_number}, пункт {point_letter}"
        else:
            point_text = f"Стаття {article_number}"

    # Build result text
    text = f"🤖 <b>Бот @VijskovePravoBot</b> визначив висновок:\n\n"

    if point and point.conclusion:
        text += f"<b>{point.conclusion}</b>"
    else:
        text += "❓ Немає даних для цього діагнозу"

    text += texts.CLOSING_NOTE

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Зберегти й почати спочатку", callback_data="pryd_start_new")],
        [InlineKeyboardButton("🏠 Повернутись на стартову сторінку", callback_data="pryd_go_home")],
        [InlineKeyboardButton("↩ Назад", callback_data="pryd_go_back")],
    ])

    # Edit current message to show results
    await _send_pryd(query, text, keyboard, context)


async def _handle_unit_select(query, db, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show requirements for selected unit."""
    parts = data.split("_")
    article_number = parts[2]
    point_letter = parts[3] if parts[3] != "none" else None
    military_unit_column = int(parts[4])

    requirements = db.get_requirements(
        article_number,
        point_letter,
        [military_unit_column]
    )

    unit = next(
        (u for u in db.get_military_units() if u.column_number == military_unit_column),
        None
    )

    if not unit:
        await query.answer("Спеціалізацію не знайдено")
        return

    text = f"<b>{unit.name}</b>\n\n"

    if requirements:
        req = requirements[0]
        if req.requirement == "НП":
            text += "❌ <b>Непридатний</b>"
        else:
            text += f"✅ <b>Придатний (Придатні)</b>\n\nРимські критерії: {req.requirement}"
    else:
        # No requirements data - get conclusion from article_points
        points = db.get_article_points(article_number)
        point = next(
            (p for p in points if p.point_letter == point_letter),
            points[0] if points else None  # Fallback to first point if no match
        )

        if point and point.conclusion:
            text += f"📋 <b>Висновок:</b>\n{point.conclusion}"
        else:
            text += "❓ Немає даних для цієї спеціалізації"

    back_data = f"pryd_point_{article_number}_{point_letter or 'none'}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💾 Зберегти результат", callback_data="pryd_save_result")],
        [InlineKeyboardButton("↩ Назад", callback_data=back_data)],
    ])

    await _send_pryd(query, text, keyboard, context)


async def _send_tables(target, table_numbers: str, context: ContextTypes.DEFAULT_TYPE = None, user_id: int = None) -> None:
    """Send all table images in one media group with caption."""
    if not table_numbers:
        return

    from telegram import InputMediaPhoto

    table_nums = [t.strip() for t in table_numbers.split(",")]
    media_group = []

    for table_num in table_nums:
        try:
            paths_to_try = [
                Path(_tables_dir) / f"table-{int(table_num):02d}.jpg",
                Path(_tables_dir) / f"Таблиця{table_num}.png",
            ]

            for table_path in paths_to_try:
                if table_path.exists():
                    with open(table_path, "rb") as f:
                        if len(media_group) == 0:
                            # First photo - add caption
                            media_group.append(
                                InputMediaPhoto(f, caption="📋 <b>Допоміжна інформація</b>", parse_mode=ParseMode.HTML)
                            )
                        else:
                            media_group.append(InputMediaPhoto(f))
                    break
        except Exception as e:
            logger.error(f"Error processing table {table_num}: {e}")

    # Send media group as one message
    if media_group:
        try:
            sent_messages = await target.reply_media_group(media_group)
            if sent_messages and context and user_id:
                # Store all helper message IDs for deletion on next step
                _init_tracker()
                if _message_tracker:
                    msg_ids = [msg.message_id for msg in sent_messages]
                    _message_tracker.set_helper_messages(user_id, COMMAND_NAME, msg_ids)
            logger.info(f"📎 Sent {len(media_group)} tables as helper message group ({len(sent_messages)} messages)")
        except Exception as e:
            logger.error(f"Error sending media group: {e}")
