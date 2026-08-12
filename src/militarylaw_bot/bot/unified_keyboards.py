"""Unified reply keyboards for all commands."""

from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup


def build_options_keyboard(options: list[str]) -> ReplyKeyboardMarkup:
    """Build reply keyboard with options and navigation buttons."""
    buttons = [[KeyboardButton(opt)] for opt in options]
    # Add navigation buttons at the bottom
    buttons.append([
        KeyboardButton("← Назад"),
        KeyboardButton("↑ Меню")
    ])
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build main menu keyboard for command selection."""
    buttons = [
        [KeyboardButton("Відстрочка")],
        # [KeyboardButton("Придатність")],
        [KeyboardButton("СЗЧ")],
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


# Vidstrochka keyboards
def vidstrochka_gate_2022() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так, до 24.02.2022 р.",
        "Ні, після 24.02.2022 р.",
        "Тільки планую укласти контракт",
    ])


def vidstrochka_contract_status() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так, на певний строк",
        "Ні, до закінчення особливого періоду",
    ])


def vidstrochka_contract_extension() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так, було",
        "Ні, не було",
    ])


def vidstrochka_contract_type() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Згідно Постанови КМУ №768 від 12.06.2026 р. (мотиваційний)",
        "Згідно Постанови КМУ №153 від 11.02.2025 р. (18-24)",
        "Інший (на загальних підставах)",
    ])


def vidstrochka_contract_term_768() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Від 6 міс.",
        "10 міс.",
        "12 міс.",
        "24 міс.",
    ])


def vidstrochka_age_at_signing() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "18-25 років",
        "25 років та старше",
    ])


def vidstrochka_contract_term() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "1 рік",
        "Більше 1 року",
    ])


def vidstrochka_discharged_before_768() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так, до 16.06.2026 р.",
        "Ні, після 16.06.2026 р.",
    ])


def vidstrochka_combat_periods() -> ReplyKeyboardMarkup:
    """Keyboard for entering number of combat periods (text input, back/menu only)."""
    buttons = [
        [KeyboardButton("← Назад"), KeyboardButton("↑ Меню")]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def text_input_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for text input (back/menu only, no option buttons)."""
    buttons = [
        [KeyboardButton("← Назад"), KeyboardButton("↑ Меню")]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def result_actions() -> ReplyKeyboardMarkup:
    """Reply keyboard for result navigation (back and menu only)."""
    buttons = [
        [KeyboardButton("← Назад"), KeyboardButton("↑ Меню")]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def result_actions_with_contract() -> ReplyKeyboardMarkup:
    """Reply keyboard for planning contract result with option to select contract."""
    buttons = [
        [KeyboardButton("📋 Обрати контракт")],
        [KeyboardButton("← Назад"), KeyboardButton("↑ Меню")]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


# Szch keyboards
def szch_formation() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "ЗСУ",
        "НГУ",
        "ДПСУ",
        "ДССТ",
    ])


def szch_yes_no() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так",
        "Ні",
    ])


def szch_awol_date() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "До 12.06.2026 включно",
        "З 13.06.2026",
        "Не знаю",
    ])


def szch_return_type() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Спрощений порядок повернення",
        "Загальний порядок повернення",
    ])


def szch_zsu_submission() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Через додаток Армія+",
        "Через центр рекрутингу",
        "Безпосередньо до обраної військової частини",
    ])


def szch_dsst_submission() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Через додаток Армія+",
        "Безпосередньо до обраної військової частини",
    ])


def szch_general_arrival() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "До своєї військової частини",
        "До ВСП",
        "До ДБР",
        "До ТЦК та СП",
        "До іншої військової частини / органу військового управління",
    ])


def szch_yes_no_unknown() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так",
        "Ні",
        "Не знаю",
    ])


def szch_consent() -> ReplyKeyboardMarkup:
    return szch_yes_no_unknown()


# Prydatnist keyboards
def prydatnist_search_method() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "🔍 Пошук по ключовому слову",
        "📚 Перегляд груп хвороб",
    ])


def prydatnist_groups_navigation(group_count: int) -> ReplyKeyboardMarkup:
    """Keyboard for navigating disease groups."""
    buttons = [
        [KeyboardButton(f"{i+1}") for i in range(min(5, group_count))]
    ]
    # Add navigation
    buttons.append([
        KeyboardButton("← Назад"),
        KeyboardButton("↑ Меню")
    ])
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def prydatnist_articles_navigation(article_count: int) -> ReplyKeyboardMarkup:
    """Keyboard for navigating articles in group."""
    buttons = []
    for i in range(0, article_count, 2):
        row = [KeyboardButton(str(i+1))]
        if i+1 < article_count:
            row.append(KeyboardButton(str(i+2)))
        buttons.append(row)

    # Add navigation
    buttons.append([
        KeyboardButton("← Назад"),
        KeyboardButton("↑ Меню")
    ])
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def prydatnist_points_navigation(point_count: int) -> ReplyKeyboardMarkup:
    """Keyboard for selecting points."""
    buttons = []
    for point in range(point_count):
        letter = chr(97 + point)  # a, b, c, etc.
        buttons.append([KeyboardButton(letter.upper())])

    # Add navigation
    buttons.append([
        KeyboardButton("← Назад"),
        KeyboardButton("↑ Меню")
    ])
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def prydatnist_units_selection() -> ReplyKeyboardMarkup:
    """Keyboard for unit selection."""
    buttons = [
        [KeyboardButton("← Назад"), KeyboardButton("↑ Меню")]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)


def prydatnist_result_actions() -> ReplyKeyboardMarkup:
    """Reply keyboard for result with option to start new search."""
    buttons = [
        [KeyboardButton("🔍 Нов пошук")],
        [KeyboardButton("← Назад"), KeyboardButton("↑ Меню")]
    ]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=False, resize_keyboard=True)
