"""Gemini inline query handler."""

from __future__ import annotations

import uuid
from typing import Any

import logfire
from aiogram import Bot, F, Router, html
from aiogram.types import (
    ChosenInlineResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
)
from aiogram.utils.i18n import gettext as _

from ..common.llm_gemini import Gemini
from ..config import settings

router = Router(name="gemini_inline")


@router.inline_query(F.query == "")
async def gemini_inline_query_empty(query: InlineQuery) -> Any:
    """Handle empty inline queries for Gemini."""
    result_id = str(uuid.uuid4())
    result = InlineQueryResultArticle(
        id=result_id,
        title=_("🤖 Ask Derp"),
        description=_("Start typing to get an AI-powered response."),
        input_message_content=InputTextMessageContent(
            message_text=html.italic(_("🤖 Please enter a prompt for Derp AI."))
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("Add Derp to your chat"),
                        url=f"https://t.me/{settings.bot_username}?startgroup=true",
                    )
                ]
            ]
        ),
    )
    await query.answer([result], cache_time=300)


@router.inline_query(F.query != "")
async def gemini_inline_query(query: InlineQuery) -> Any:
    """Handle inline queries for Gemini."""
    result_id = str(uuid.uuid4())
    user_input = query.query[:200] or "..."

    result = InlineQueryResultArticle(
        id=result_id,
        title=_("🤖 Ask Derp"),
        description=_("Get an AI-powered response for: {user_input}").format(
            user_input=user_input
        ),
        input_message_content=InputTextMessageContent(
            message_text=html.italic(
                _("🧠 Thinking about: {user_input}").format(user_input=user_input)
            )
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("Add Derp to your chat"),
                        url=f"https://t.me/{settings.bot_username}?startgroup=true",
                    )
                ]
            ]
        ),
    )
    await query.answer(
        [result],
        button=InlineQueryResultsButton(
            text=_("Start personal chat"),
            start_parameter="start",
        ),
        cache_time=300,
    )


@router.chosen_inline_result()
async def gemini_chosen_inline_result(chosen_result: ChosenInlineResult, bot: Bot):
    """Handle chosen inline results for Gemini."""
    if not chosen_result.inline_message_id:
        return

    user_info = chosen_result.from_user.model_dump_json(
        exclude_defaults=True, exclude_none=True, exclude_unset=True
    )
    prompt = f"User: {user_info}\nQuery: {chosen_result.query}"

    gemini = Gemini()
    request = (
        gemini.create_request()
        .with_text(prompt)
        .with_google_search()
        .with_url_context()
    )

    try:
        result = await request.execute()
        if result.has_content:
            response_text = (
                f"Prompt: {chosen_result.query}\n\nResponse:\n{result.full_text}"[:4096]
            )
            await bot.edit_message_text(
                response_text,
                inline_message_id=chosen_result.inline_message_id,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=_("Add Derp to your chat"),
                                url=f"https://t.me/{settings.bot_username}?startgroup=true",
                            )
                        ]
                    ]
                ),
            )
        else:
            await bot.edit_message_text(
                _("🤯 My circuits are a bit tangled. I couldn't generate a response."),
                inline_message_id=chosen_result.inline_message_id,
            )
    except Exception:
        logfire.exception("Error in Gemini inline handler")
        await bot.edit_message_text(
            _("😅 Something went wrong with Gemini. I couldn't process that."),
            inline_message_id=chosen_result.inline_message_id,
        )
