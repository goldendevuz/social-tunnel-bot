"""
Все клавиатуры BigFatherBot: reply и inline.
"""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from storage import ManagedBotInfo


# ─────────────────── Reply-клавиатура (главное меню) ───────────────────

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🤖 Создать бота"),
                KeyboardButton(text="📋 Мои боты"),
            ],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )


# ─────────────────── Inline: список всех управляемых ботов ───────────────────

def bots_list_kb(bots: list[ManagedBotInfo]) -> InlineKeyboardMarkup:
    """Список ботов пользователя — каждый бот отдельной кнопкой."""
    builder = InlineKeyboardBuilder()
    for bot in bots:
        builder.row(
            InlineKeyboardButton(
                text=f"🤖 {bot.first_name} (@{bot.username})",
                callback_data=f"bot_info:{bot.bot_id}",
            )
        )
    if not bots:
        builder.row(
            InlineKeyboardButton(
                text="➕ Создать первого бота",
                callback_data="create_bot",
            )
        )
    return builder.as_markup()


# ─────────────────── Inline: управление конкретным ботом ───────────────────

def bot_actions_kb(bot_info: ManagedBotInfo) -> InlineKeyboardMarkup:
    """
    Панель управления конкретным управляемым ботом.

    Демонстрирует все доступные операции Bot API 9.6:
    • Открыть — inline-ссылка t.me/username
    • Получить токен — getManagedBotToken
    • Обновить токен — replaceManagedBotToken
    • Изменить имя / описание / краткое описание — через токен бота
    """
    builder = InlineKeyboardBuilder()

    # Открыть бота по inline-ссылке
    builder.row(
        InlineKeyboardButton(
            text="🔗 Открыть бота",
            url=f"https://t.me/{bot_info.username}",
        )
    )

    # Операции с токеном (Bot API 9.6)
    builder.row(
        InlineKeyboardButton(
            text="🔑 Получить токен",
            callback_data=f"get_token:{bot_info.bot_id}",
        ),
        InlineKeyboardButton(
            text="🔄 Обновить токен",
            callback_data=f"replace_token:{bot_info.bot_id}",
        ),
    )

    # Редактирование настроек через токен управляемого бота
    builder.row(
        InlineKeyboardButton(
            text="✏️ Имя",
            callback_data=f"edit_name:{bot_info.bot_id}",
        ),
        InlineKeyboardButton(
            text="📝 Описание",
            callback_data=f"edit_desc:{bot_info.bot_id}",
        ),
        InlineKeyboardButton(
            text="📋 Краткое описание",
            callback_data=f"edit_short_desc:{bot_info.bot_id}",
        ),
    )

    # Назад к списку
    builder.row(
        InlineKeyboardButton(
            text="⬅️ К списку ботов",
            callback_data="list_bots",
        )
    )

    return builder.as_markup()


# ─────────────────── Inline: подтверждение замены токена ───────────────────

def confirm_replace_token_kb(bot_id: int) -> InlineKeyboardMarkup:
    """Запрашиваем подтверждение, так как старый токен инвалидируется."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, заменить",
            callback_data=f"confirm_replace_token:{bot_id}",
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=f"bot_info:{bot_id}",
        ),
    )
    return builder.as_markup()


# ─────────────────── Inline: отмена FSM-действия ───────────────────

def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")
    )
    return builder.as_markup()
