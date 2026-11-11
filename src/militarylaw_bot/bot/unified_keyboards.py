"""Unified reply keyboards for all commands."""

from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup

# Shown in the message input field, so the user sees whether to tap or type
PICK_BUTTON_PLACEHOLDER = "👇 Натисніть кнопку внизу"
TYPE_NUMBER_PLACEHOLDER = "⌨️ Напишіть число"


def build_grid_keyboard(
    options: list[str], per_row: int, placeholder: str = PICK_BUTTON_PLACEHOLDER
) -> ReplyKeyboardMarkup:
    """Reply keyboard with options laid out per_row in a row, plus navigation buttons.

    The keyboard stays open (is_persistent) and the input field placeholder says
    whether to tap a button or type.
    """
    buttons = [
        [KeyboardButton(opt) for opt in options[i:i + per_row]]
        for i in range(0, len(options), per_row)
    ]
    buttons.append([KeyboardButton("← Назад"), KeyboardButton("↑ Меню")])
    return ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=False,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=placeholder,
    )


def build_options_keyboard(options: list[str]) -> ReplyKeyboardMarkup:
    """Build reply keyboard with one option per row and navigation buttons."""
    return build_grid_keyboard(options, per_row=1)


VIDSTROCHKA_BUTTON = "Відстрочка після звільнення у зв'язку із закінченням контракту"
# Earlier labels that may still be on users' persistent menu keyboards
VIDSTROCHKA_LEGACY_BUTTONS = ("Відстрочка", "Відстрочка після звільнення по закінченню контракту")
PRYDATNIST_BUTTON = "ВЛК"
PRYDATNIST_LEGACY_BUTTONS = ("Придатність",)


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build main menu keyboard for command selection."""
    buttons = [
        [KeyboardButton(VIDSTROCHKA_BUTTON)],
        [KeyboardButton(PRYDATNIST_BUTTON)],
        [KeyboardButton("СЗЧ")],
        # [KeyboardButton("Переведення")],  # temporarily hidden
    ]
    return ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=False,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=PICK_BUTTON_PLACEHOLDER,
    )


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


def text_input_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for typing a number (back/menu only, no option buttons)."""
    return build_grid_keyboard([], per_row=1, placeholder=TYPE_NUMBER_PLACEHOLDER)


def result_actions() -> ReplyKeyboardMarkup:
    """Reply keyboard for result navigation (back and menu only)."""
    return build_grid_keyboard([], per_row=1)


def vidstrochka_registration_question() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["Так", "Ні"])


def result_actions_with_contract() -> ReplyKeyboardMarkup:
    """Reply keyboard for planning contract result with option to select contract."""
    return build_grid_keyboard(["📋 Обрати контракт"], per_row=1)


# Szch keyboards
def szch_first_time() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["Так, вперше", "Ні, не вперше"])


# Transfer keyboards
def transfer_formation() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["ЗСУ", "НГУ", "ДПСУ", "ДССТ"])


def transfer_service_type() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["За контрактом", "За мобілізацією"])


def transfer_initiative() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["З власної ініціативи", "За рішенням командування"])


def transfer_yes_no() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["Так", "Ні"])


def transfer_graduate_year() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так, ще не минув 1 рік після випуску",
        "Так, уже минув 1 рік",
        "Ні, я не навчався у ВВНЗ / навчальному підрозділі",
    ])


def transfer_zsu_ground() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Звичайне переведення за власною ініціативою",
        "За станом здоров'я військовослужбовця",
        "За станом здоров'я члена сім'ї",
        "За сімейними обставинами",
        "Через родинну підлеглість / конфлікт інтересів",
        "Через скасування допуску до держтаємниці",
        "Для більш доцільного використання за фахом / досвідом",
    ])


def transfer_dpsu_ground() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Звичайне переведення за особистим проханням",
        "За станом здоров'я",
        "За сімейними обставинами",
        "На нижчу посаду / менше навантаження",
        "Через службову необхідність",
    ])


def transfer_position_level() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Рівнозначна посада",
        "Нижча посада / менше навантаження",
        "Вища посада",
    ])


def transfer_unit_type() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["Бойова", "Тилова", "Не знаю"])


def transfer_current_unit_duration() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["Менше 6 місяців", "Більше 6 місяців"])


def transfer_previous_transfer_gap() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Так, минув",
        "Ні, ще не минув",
        "Це перше переведення",
    ])


def transfer_rear_destination() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["До бойової частини", "До іншої тилової частини"])


def transfer_combat_goal() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "До іншої бойової частини",
        "За висновком ВЛК до частини забезпечення",
        "До тилової частини без висновку ВЛК",
    ])


def transfer_yes_no_unknown() -> ReplyKeyboardMarkup:
    return build_options_keyboard(["Так", "Ні", "Не знаю"])


def transfer_family_circumstance() -> ReplyKeyboardMarkup:
    return build_options_keyboard([
        "Потрібен догляд за батьками",
        "Потрібен догляд за дружиною / чоловіком",
        "Потрібен догляд за особою, яка виховувала з дитинства",
        "Інші підтверджені сімейні обставини",
    ])
