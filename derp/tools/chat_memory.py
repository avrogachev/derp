"""Chat memory management tool for PydanticAI agents."""

from aiogram import html
from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from ..common.database import get_database_client
from ..queries.update_chat_settings_async_edgeql import update_chat_settings
from .deps import AgentDeps


async def update_chat_memory(ctx: RunContext[AgentDeps], full_memory: str) -> str:
    # Validate memory length
    if len(full_memory) > 1024:
        raise Exception(
            f"Memory exceeds 1024 characters limit. "
            f"Current length is {len(full_memory)} characters. "
            f"Please provide a shorter memory state."
        )

    # Update memory in database
    db_client = get_database_client()
    async with db_client.get_executor() as executor:
        await update_chat_settings(
            executor, chat_id=ctx.deps.message.chat.id, llm_memory=full_memory.strip()
        )
    await ctx.deps.message.reply(
        "(System message) Memory updated:\n"
        + html.expandable_blockquote(html.quote(full_memory.strip()))
    )

    return f"Memory updated successfully. New memory length: {len(full_memory)} characters."


def update_chat_memory_tool() -> Tool:
    """Creates a chat memory management tool.

    This tool allows the AI agent to update the complete chat memory state.
    The memory has a 1024 character limit.
    """
    return Tool(
        update_chat_memory,
        name="update_chat_memory",
        description=(
            "Use this to save the entire memory state after combining existing memory with new facts. "
            "The memory has a 1024 character limit. "
            "Keep it concise and remove less important information if the limit would be exceeded."
        ),
    )
