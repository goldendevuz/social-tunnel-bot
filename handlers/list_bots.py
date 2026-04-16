"""
Обработчики для просмотра списка управляемых ботов и информации о каждом.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import bot_actions_kb, bots_list_kb
from storage import Storage

router = Router()


async def _render_list(storage: Storage, owner_id: int) -> tuple[str, object]:
    """Возвращает (текст, клавиатура) для списка ботов пользователя."""
    bots = storage.all_by_owner(owner_id)
    if bots:
        text = f"📋 <b>Твои управляемые боты</b> ({len(bots)} шт.)\n\nВыбери бота:"
    else:
        text = (
            "📭 У тебя пока нет управляемых ботов.\n\n"
            "Нажми <b>🤖 Создать бота</b>, чтобы создать первого!"
        )
    return text, bots_list_kb(bots)


@router.message(F.text == "📋 Мои боты")
@router.message(Command("list"))
async def show_bots_list(message: Message, storage: Storage) -> None:
    text, kb = await _render_list(storage, message.from_user.id)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "list_bots")
async def show_bots_list_cb(callback: CallbackQuery, storage: Storage) -> None:
    text, kb = await _render_list(storage, callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("bot_info:"))
async def show_bot_info(callback: CallbackQuery, storage: Storage) -> None:
    """Показываем детальную карточку бота с панелью управления."""
    bot_id = int(callback.data.split(":")[1])
    info = storage.get(bot_id)

    if not info:
        await callback.answer("❌ Бот не найден в хранилище", show_alert=True)
        return

    await callback.message.edit_text(
        f"🤖 <b>{info.first_name}</b>\n"
        f"👤 @{info.username}\n"
        f"🆔 ID: <code>{info.bot_id}</code>\n"
        f"📅 Создан: {info.created_at[:10]}\n\n"
        "Выбери действие:",
        reply_markup=bot_actions_kb(info),
    )
    await callback.answer()
