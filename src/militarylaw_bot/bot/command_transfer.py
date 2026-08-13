"""Переведення (Transfer) command implementation."""

from __future__ import annotations

import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from militarylaw_bot.bot import texts
from militarylaw_bot.bot.global_session import CommandType, get_session
from militarylaw_bot.bot.unified_keyboards import (
    transfer_formation, transfer_service_type, transfer_initiative,
    transfer_graduate_year, transfer_zsu_ground, transfer_dpsu_ground,
    transfer_position_level, transfer_unit_type, transfer_current_unit_duration,
    transfer_previous_transfer_gap, transfer_rear_destination, transfer_combat_goal,
    transfer_yes_no, transfer_yes_no_unknown, transfer_family_circumstance,
    result_actions,
)
from militarylaw_bot.bot.transfer_session import get_next_step

logger = logging.getLogger(__name__)


def get_keyboard_for_step(step: str, answers: dict):
    """Get appropriate keyboard for a step."""
    if step == "transfer_formation":
        return transfer_formation()
    elif step == "transfer_service_type":
        return transfer_service_type()
    elif step == "transfer_initiative":
        return transfer_initiative()
    elif step == "transfer_graduate_year":
        return transfer_graduate_year()
    elif step == "transfer_unit_type":
        return transfer_unit_type()
    elif step == "transfer_unit_type_unknown":
        return result_actions()
    elif step == "transfer_current_unit_duration":
        return transfer_current_unit_duration()
    elif step == "transfer_previous_transfer_gap":
        return transfer_previous_transfer_gap()
    elif step == "transfer_zsu_ground":
        return transfer_zsu_ground()
    elif step == "transfer_dpsu_ground":
        return transfer_dpsu_ground()
    elif step == "transfer_position_level":
        return transfer_position_level()
    elif step == "transfer_rear_destination":
        return transfer_rear_destination()
    elif step == "transfer_combat_goal":
        return transfer_combat_goal()
    elif step == "transfer_recommendation_letter":
        return transfer_yes_no()
    elif step == "transfer_medical_conclusion":
        return transfer_yes_no()
    elif step == "transfer_family_circumstance":
        return transfer_family_circumstance()
    elif step == "transfer_supporting_documents":
        return transfer_yes_no()
    elif step == "transfer_officer_status":
        return transfer_yes_no()
    elif step == "transfer_command_approval":
        return transfer_yes_no()
    elif step == "transfer_command_health_obstacle":
        return transfer_yes_no_unknown()
    elif step == "transfer_command_family_care_need":
        return transfer_yes_no_unknown()
    else:
        return transfer_formation()


def get_text_for_step(step: str) -> str:
    """Get question text for a step."""
    step_texts = {
        "transfer_formation": texts.TRANSFER_FORMATION_QUESTION,
        "transfer_service_type": texts.TRANSFER_SERVICE_TYPE,
        "transfer_initiative": texts.TRANSFER_INITIATIVE,
        "transfer_graduate_year": texts.TRANSFER_GRADUATE_YEAR,
        "transfer_unit_type": texts.TRANSFER_UNIT_TYPE,
        "transfer_unit_type_unknown": texts.TRANSFER_UNIT_TYPE_UNKNOWN,
        "transfer_current_unit_duration": texts.TRANSFER_CURRENT_UNIT_DURATION,
        "transfer_previous_transfer_gap": texts.TRANSFER_PREVIOUS_TRANSFER_GAP,
        "transfer_zsu_ground": texts.TRANSFER_ZSU_GROUND,
        "transfer_dpsu_ground": texts.TRANSFER_DPSU_GROUND,
        "transfer_position_level": texts.TRANSFER_POSITION_LEVEL,
        "transfer_rear_destination": texts.TRANSFER_REAR_DESTINATION,
        "transfer_combat_goal": texts.TRANSFER_COMBAT_GOAL,
        "transfer_recommendation_letter": texts.TRANSFER_RECOMMENDATION_LETTER,
        "transfer_medical_conclusion": texts.TRANSFER_MEDICAL_CONCLUSION,
        "transfer_family_circumstance": texts.TRANSFER_FAMILY_CIRCUMSTANCE,
        "transfer_supporting_documents": texts.TRANSFER_SUPPORTING_DOCUMENTS,
        "transfer_officer_status": texts.TRANSFER_OFFICER_STATUS,
        "transfer_command_approval": texts.TRANSFER_COMMAND_APPROVAL,
        "transfer_command_health_obstacle": texts.TRANSFER_COMMAND_HEALTH_OBSTACLE,
        "transfer_command_family_care_need": texts.TRANSFER_COMMAND_FAMILY_CARE_NEED,
    }
    return step_texts.get(step, "")


async def handle_transfer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start transfer command."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)

    session.current_command = CommandType.TRANSFER
    session.answers.clear()
    session.step = "transfer_formation"
    session.push_history()

    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
    await update.message.reply_text(
        texts.TRANSFER_FORMATION_QUESTION,
        reply_markup=transfer_formation(),
        parse_mode="HTML",
    )
    return "transfer_formation"


async def handle_transfer_generic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Generic handler for transfer steps that just transitions to next step."""
    chat_id = update.effective_chat.id
    session = get_session(chat_id)
    text = update.message.text.strip()

    # Don't process navigation buttons - let wrapper handle them
    if text in ["← Назад", "↑ Меню"]:
        return session.step

    # Store answer based on current step
    step_to_key = {
        "transfer_formation": "formation",
        "transfer_service_type": "service_type",
        "transfer_initiative": "initiative",
        "transfer_graduate_year": "graduate_year",
        "transfer_unit_type": "unit_type",
        "transfer_current_unit_duration": "current_unit_duration",
        "transfer_previous_transfer_gap": "previous_transfer_gap",
        "transfer_zsu_ground": "zsu_ground",
        "transfer_dpsu_ground": "dpsu_ground",
        "transfer_position_level": "position_level",
        "transfer_rear_destination": "destination",
        "transfer_combat_goal": "destination",
        "transfer_recommendation_letter": "recommendation_letter",
        "transfer_medical_conclusion": "medical_conclusion",
        "transfer_family_circumstance": "family_circumstance",
        "transfer_supporting_documents": "supporting_documents",
        "transfer_officer_status": "officer_status",
        "transfer_command_approval": "command_approval",
        "transfer_command_health_obstacle": "command_health_obstacle",
        "transfer_command_family_care_need": "command_family_care_need",
    }

    key = step_to_key.get(session.step)
    if key:
        session.answers[key] = text

    # Get next step
    next_step = get_next_step(session.step, text, session.answers)

    if next_step == "transfer_result_graduate_restriction":
        session.push_history()
        session.step = "transfer_result"
        result_text = texts.build_transfer_graduate_restriction_result(session.answers)
        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            result_text,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "transfer_result"

    if next_step == "transfer_result":
        session.push_history()
        session.step = "transfer_result"

        # Determine result type based on formation, initiative, and ground
        formation = session.answers.get("formation", "")
        initiative = session.answers.get("initiative", "")
        dpsu_ground = session.answers.get("dpsu_ground", "")

        # DPSU service necessity (Через службову необхідність) uses command result
        if formation == "ДПСУ" and dpsu_ground == "Через службову необхідність":
            result_text = texts.build_dpsu_command_result(session.answers)
        # Command-initiated transfers (За рішенням командування) for ZSU/НГУ/ДССТ
        elif initiative == "За рішенням командування":
            result_text = texts.build_transfer_command_decision_result(session.answers)
        # DPSU-specific result for own initiative
        elif formation == "ДПСУ":
            result_text = texts.build_dpsu_result(session.answers)
        # General ZSU/НГУ/ДССТ result for own initiative
        else:
            result_text = texts.build_transfer_result(session.answers)

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        await update.message.reply_text(
            result_text,
            reply_markup=result_actions(),
            parse_mode="HTML",
        )
        return "transfer_result"

    if next_step is None:
        return session.step

    if next_step:
        # Push history BEFORE changing step so we can return to current step
        session.push_history()
        session.step = next_step

        await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        step_text = get_text_for_step(next_step)
        keyboard = get_keyboard_for_step(next_step, session.answers)
        await update.message.reply_text(
            step_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return next_step

    return session.step
