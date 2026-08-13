"""Transfer (Переведення) session management - logic for transfer flow."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TransferSession:
    """Session state for transfer flow."""
    answers: dict = None

    def __post_init__(self):
        if self.answers is None:
            self.answers = {}

    def reset(self):
        """Reset session to initial state."""
        self.answers.clear()


# Transfer flow constants
FORMATION_OPTIONS = ["ЗСУ", "НГУ", "ДПСУ", "ДССТ"]
SERVICE_TYPE_OPTIONS = ["За контрактом", "За мобілізацією"]
INITIATIVE_OPTIONS = ["З власної ініціативи", "За рішенням командування"]
UNIT_TYPE_OPTIONS = ["Бойова", "Тилова", "Не знаю"]
REAR_DESTINATION_OPTIONS = ["До бойової частини", "До іншої тилової частини"]
COMBAT_GOAL_OPTIONS = [
    "До іншої бойової частини",
    "За висновком ВЛК до частини забезпечення",
    "До тилової частини без висновку ВЛК",
]
CURRENT_UNIT_DURATION_OPTIONS = ["Менше 6 місяців", "Більше 6 місяців"]
PREVIOUS_TRANSFER_GAP_OPTIONS = [
    "Так, минув",
    "Ні, ще не минув",
    "Це перше переведення",
]
RECOMMENDATION_LETTER_OPTIONS = ["Так", "Ні"]
COMMAND_APPROVAL_OPTIONS = ["Так", "Ні"]
GRADUATE_YEAR_OPTIONS = [
    "Так, ще не минув 1 рік після випуску",
    "Так, уже минув 1 рік",
    "Ні, я не навчався у ВВНЗ / навчальному підрозділі",
]
ZSU_GROUND_OPTIONS = [
    "Звичайне переведення за власною ініціативою",
    "За станом здоров'я військовослужбовця",
    "За станом здоров'я члена сім'ї",
    "За сімейними обставинами",
    "Через родинну підлеглість / конфлікт інтересів",
    "Через скасування допуску до держтаємниці",
    "Для більш доцільного використання за фахом / досвідом",
]
DPSU_GROUND_OPTIONS = [
    "Звичайне переведення за особистим проханням",
    "За станом здоров'я",
    "За сімейними обставинами",
    "На нижчу посаду / менше навантаження",
    "Через службову необхідність",
]
POSITION_LEVEL_OPTIONS = [
    "Рівнозначна посада",
    "Нижча посада / менше навантаження",
    "Вища посада",
]
MEDICAL_CONCLUSION_OPTIONS = ["Так", "Ні"]
FAMILY_CIRCUMSTANCE_OPTIONS = [
    "Потрібен догляд за батьками",
    "Потрібен догляд за дружиною / чоловіком",
    "Потрібен догляд за особою, яка виховувала з дитинства",
    "Інші підтверджені сімейні обставини",
]
SUPPORTING_DOCUMENTS_OPTIONS = ["Так", "Ні"]
OFFICER_STATUS_OPTIONS = ["Так", "Ні"]
FAMILY_CARE_OPTIONS = ["Так", "Ні", "Не знаю"]
HEALTH_OBSTACLE_OPTIONS = ["Так", "Ні", "Не знаю"]
CURRENT_UNIT_NAME_OPTIONS = []  # Free text input
CURRENT_UNIT_SERVICE_DURATION_OPTIONS = ["Менше 6 місяців", "Від 6 місяців до 1 року", "Більше 1 року"]


def is_first_year_graduate(answers: dict) -> bool:
    """Check if user is a first-year graduate (graduated less than 1 year ago)."""
    graduate_year = answers.get("graduate_year", "")
    return graduate_year == "Так, ще не минув 1 рік після випуску"


def is_exceptional_graduate_ground(answers: dict) -> bool:
    """Check if selected ground is exceptional for first-year graduates."""
    formation = answers.get("formation", "")
    if formation == "ЗСУ":
        ground = answers.get("zsu_ground", "")
        return ground in [
            "За станом здоров'я військовослужбовця",
            "За станом здоров'я члена сім'ї",
            "За сімейними обставинами",
            "Через родинну підлеглість / конфлікт інтересів",
        ]
    else:
        ground = answers.get("dpsu_ground", "")
        return ground in [
            "За станом здоров'я",
            "За сімейними обставинами",
        ]


def get_next_step(current_step: str, answer: str, answers: dict) -> str | None:
    """Determine next step based on current step and answer."""
    if current_step == "transfer_formation":
        return "transfer_service_type"
    elif current_step == "transfer_service_type":
        return "transfer_initiative"
    elif current_step == "transfer_initiative":
        # Check if "За рішенням командування"
        initiative = answer
        if initiative == "За рішенням командування":
            return "transfer_command_health_obstacle"

        # For own initiative, route based on formation
        formation = answers.get("formation", "")
        if formation in ["ЗСУ", "НГУ", "ДССТ"]:
            return "transfer_graduate_year"
        elif formation == "ДПСУ":
            return "transfer_dpsu_ground"
        else:
            return "transfer_unit_type"
    elif current_step == "transfer_graduate_year":
        formation = answers.get("formation", "")
        if formation in ["ЗСУ", "НГУ", "ДССТ"]:
            return "transfer_zsu_ground"
        # ДПСУ doesn't use graduate_year step at all
    elif current_step == "transfer_unit_type":
        # If user doesn't know unit type, show info and return to this step
        if answer == "Не знаю":
            return "transfer_unit_type_unknown"
        return "transfer_current_unit_duration"
    elif current_step == "transfer_unit_type_unknown":
        # After showing info, return to unit type question
        return "transfer_unit_type"
    elif current_step == "transfer_current_unit_duration":
        return "transfer_previous_transfer_gap"
    elif current_step == "transfer_previous_transfer_gap":
        # After previous transfer gap, route based on unit type
        unit_type = answers.get("unit_type", "")
        if unit_type == "Тилова":
            return "transfer_rear_destination"
        else:
            # Бойова or Не знаю
            return "transfer_combat_goal"
    elif current_step == "transfer_zsu_ground":
        ground = answer

        # Check if first-year graduate with non-exceptional ground
        if is_first_year_graduate(answers) and not is_exceptional_graduate_ground(answers):
            return "transfer_result_graduate_restriction"

        # All grounds go through position_level question first
        return "transfer_position_level"
    elif current_step == "transfer_dpsu_ground":
        ground = answer

        # Check if first-year graduate with non-exceptional ground
        if is_first_year_graduate(answers) and not is_exceptional_graduate_ground(answers):
            return "transfer_result_graduate_restriction"

        # "Через службову необхідність" goes to command_health_obstacle (like command-initiated transfers)
        if ground == "Через службову необхідність":
            return "transfer_command_health_obstacle"

        # All other grounds go through position_level question first
        return "transfer_position_level"
    elif current_step == "transfer_position_level":
        # Determine which ground was selected based on formation
        formation = answers.get("formation", "")
        if formation in ["ЗСУ", "НГУ", "ДССТ"]:
            ground = answers.get("zsu_ground", "")
        else:  # ДПСУ
            ground = answers.get("dpsu_ground", "")

        # For ЗСУ/НГУ/ДССТ formations
        if formation in ["ЗСУ", "НГУ", "ДССТ"]:
            if ground == "Звичайне переведення за власною ініціативою":
                return "transfer_unit_type"
            elif ground in ["За станом здоров'я військовослужбовця", "За станом здоров'я члена сім'ї"]:
                return "transfer_medical_conclusion"
            elif ground == "За сімейними обставинами":
                return "transfer_family_circumstance"
            elif ground in ["Через родинну підлеглість / конфлікт інтересів", "Через скасування допуску до держтаємниці"]:
                return "transfer_recommendation_letter"
            elif ground == "Для більш доцільного використання за фахом / досвідом":
                return "transfer_officer_status"
            else:
                return "transfer_recommendation_letter"

        # For ДПСУ formation
        else:
            if ground == "Звичайне переведення за особистим проханням":
                return "transfer_unit_type"
            elif ground == "За станом здоров'я":
                return "transfer_medical_conclusion"
            elif ground == "За сімейними обставинами":
                return "transfer_family_circumstance"
            elif ground == "На нижчу посаду / менше навантаження":
                return "transfer_medical_conclusion"
            else:
                return "transfer_recommendation_letter"
    elif current_step == "transfer_rear_destination":
        # After rear destination, check if "До тилової частини без висновку ВЛК"
        destination = answer
        if destination == "До тилової частини без висновку ВЛК":
            return "transfer_command_approval"
        return "transfer_recommendation_letter"
    elif current_step == "transfer_combat_goal":
        # After combat goal, check if "До тилової частини без висновку ВЛК"
        destination = answer
        if destination == "До тилової частини без висновку ВЛК":
            return "transfer_command_approval"
        return "transfer_recommendation_letter"
    elif current_step == "transfer_command_approval":
        # After command approval, go to recommendation letter
        return "transfer_recommendation_letter"
    elif current_step == "transfer_officer_status":
        # After officer status, go to recommendation letter
        return "transfer_recommendation_letter"
    elif current_step == "transfer_medical_conclusion":
        return "transfer_recommendation_letter"
    elif current_step == "transfer_recommendation_letter":
        return "transfer_result"
    elif current_step == "transfer_family_circumstance":
        return "transfer_supporting_documents"
    elif current_step == "transfer_supporting_documents":
        # After supporting documents for family circumstances, skip medical conclusion
        # and go straight to recommendation letter
        return "transfer_recommendation_letter"
    elif current_step == "transfer_command_health_obstacle":
        # After command health obstacle, go to family care need
        return "transfer_command_family_care_need"
    elif current_step == "transfer_command_family_care_need":
        # After family care need, go to result for command-initiated transfer
        return "transfer_result"
    else:
        return None
