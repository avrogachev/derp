from aiogram import Router, html
from aiogram.filters import Command
from aiogram.types import Message

from derp.common.database import DatabaseClient
from derp.queries.chat_settings_async_edgeql import ChatSettingsResult
from derp.queries.update_chat_settings_async_edgeql import update_chat_settings

router = Router(name="chat_settings")


@router.message(Command("settings"))
async def cmd_show_settings(
    message: Message,
    chat_settings: ChatSettingsResult,
) -> None:
    """Show current chat settings."""
    settings_text = "📋 Chat Settings:\n\n"

    if chat_settings.llm_memory:
        settings_text += (
            f"🧠 LLM Memory: {html.blockquote(html.quote(chat_settings.llm_memory))}\n"
        )
    else:
        settings_text += "🧠 LLM Memory: Not set\n"

    return await message.reply(settings_text)


@router.message(Command("set_memory"))
async def cmd_set_memory(
    message: Message,
    db: DatabaseClient,
) -> None:
    """Set LLM memory for the chat."""

    # Extract memory text from command
    command_args = message.text.split(maxsplit=1)
    if len(command_args) < 2:
        await message.answer(
            "Usage: /set_memory <memory_text>\n"
            "Example: /set_memory This chat is about Python programming"
        )
        return

    memory_text = command_args[1].strip()

    try:
        # Validate length (our dataclass will also validate this)
        if len(memory_text) > 1024:
            await message.answer("❌ Memory text cannot exceed 1024 characters.")
            return

        # Update in database
        async with db.get_executor() as executor:
            await update_chat_settings(
                executor, chat_id=message.chat.id, llm_memory=memory_text
            )

        await message.answer(f"✅ LLM memory updated:\n\n{memory_text}")

    except Exception as e:
        await message.answer(f"❌ Failed to update memory: {str(e)}")


@router.message(Command("clear_memory"))
async def cmd_clear_memory(
    message: Message,
    db: DatabaseClient,
) -> None:
    """Clear LLM memory for the chat."""

    try:
        async with db.get_executor() as executor:
            await update_chat_settings(
                executor, chat_id=message.chat.id, llm_memory=None
            )

        await message.answer("✅ LLM memory cleared.")

    except Exception as e:
        await message.answer(f"❌ Failed to clear memory: {str(e)}")
