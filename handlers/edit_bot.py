"""
Обработчики для редактирования настроек управляемых ботов.

Ключевая концепция Bot API 9.6:
────────────────────────────────
Чтобы изменить настройки управляемого бота, нужно:
  1. Получить его токен: getManagedBotToken(managed_bot_id) → str
  2. Создать временный Bot-инстанс с этим токеном
  3. Вызвать нужный метод на этом инстансе
  4. Закрыть сессию временного инстанса

Это принципиально отличается от обычного управления ботом:
мы буквально «становимся» управляемым ботом на время вызова.
"""
import logging

from aiogram import Router, F, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import bot_actions_kb, cancel_kb, confirm_replace_token_kb
from states import EditBotStates
from storage import Storage

router = Router()
logger = logging.getLogger(__name__)


async def _get_managed_bot(main_bot: Bot, managed_bot_id: int) -> Bot:
    """
    Создаём временный Bot-инстанс для управляемого бота.

    Шаги:
    1. Вызываем getManagedBotToken — метод Bot API 9.6
    2. Оборачиваем токен в новый Bot-инстанс aiogram

    После использования ОБЯЗАТЕЛЬНО закрыть: await managed_bot.session.close()
    """
    token = await main_bot.get_managed_bot_token(managed_bot_id=managed_bot_id)
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


# ═══════════════════════════════════════════════════════════
#  ПОЛУЧЕНИЕ ТОКЕНА
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("get_token:"))
async def get_token(callback: CallbackQuery, bot: Bot, storage: Storage) -> None:
    """
    getManagedBotToken — получаем токен управляемого бота.

    В образовательных целях показываем токен пользователю.
    В реальных проектах токен следует хранить в защищённом хранилище.
    """
    bot_id = int(callback.data.split(":")[1])
    info = storage.get(bot_id)
    if not info:
        await callback.answer("❌ Бот не найден", show_alert=True)
        return

    await callback.answer("⏳ Получаю токен...")

    try:
        # ← Bot API 9.6: getManagedBotToken
        token = await bot.get_managed_bot_token(managed_bot_id=bot_id)

        await callback.message.answer(
            f"🔑 <b>Токен бота @{info.username}</b>\n\n"
            f"<code>{token}</code>\n\n"
            f"⚠️ <i>Храни токен в тайне! Тот, кто знает токен, "
            f"полностью управляет ботом.</i>\n\n"
            f"💡 <b>API-вызов:</b>\n"
            f"<code>getManagedBotToken(managed_bot_id={bot_id})</code>"
        )
    except Exception as e:
        logger.exception("get_managed_bot_token failed")
        await callback.message.answer(f"❌ Ошибка получения токена:\n<code>{e}</code>")


# ═══════════════════════════════════════════════════════════
#  ЗАМЕНА ТОКЕНА
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("replace_token:"))
async def ask_confirm_replace_token(callback: CallbackQuery, storage: Storage) -> None:
    """Запрашиваем подтверждение перед заменой — старый токен будет инвалидирован."""
    bot_id = int(callback.data.split(":")[1])
    info = storage.get(bot_id)
    if not info:
        await callback.answer("❌ Бот не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Заменить токен @{info.username}?</b>\n\n"
        f"Старый токен станет <b>недействительным</b> сразу же.\n"
        f"Если бот запущен со старым токеном — он перестанет работать.\n\n"
        f"Продолжить?",
        reply_markup=confirm_replace_token_kb(bot_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_replace_token:"))
async def do_replace_token(callback: CallbackQuery, bot: Bot, storage: Storage) -> None:
    """
    replaceManagedBotToken — генерируем новый токен для управляемого бота.

    Важно: после вызова старый токен сразу инвалидируется!
    Это удобно для ротации ключей или при утечке токена.
    """
    bot_id = int(callback.data.split(":")[1])
    info = storage.get(bot_id)
    if not info:
        await callback.answer("❌ Бот не найден", show_alert=True)
        return

    await callback.answer("⏳ Генерирую новый токен...")

    try:
        # ← Bot API 9.6: replaceManagedBotToken
        new_token = await bot.replace_managed_bot_token(managed_bot_id=bot_id)

        await callback.message.edit_text(
            f"✅ <b>Токен @{info.username} заменён!</b>\n\n"
            f"🔑 Новый токен:\n<code>{new_token}</code>\n\n"
            f"❌ Старый токен теперь <b>недействителен</b>.\n\n"
            f"💡 <b>API-вызов:</b>\n"
            f"<code>replaceManagedBotToken(managed_bot_id={bot_id})</code>",
            reply_markup=bot_actions_kb(info),
        )
    except Exception as e:
        logger.exception("replace_managed_bot_token failed")
        await callback.message.edit_text(
            f"❌ Ошибка замены токена:\n<code>{e}</code>",
            reply_markup=bot_actions_kb(info),
        )


# ═══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ ИМЕНИ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("edit_name:"))
async def start_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    bot_id = int(callback.data.split(":")[1])
    await state.set_state(EditBotStates.editing_name)
    await state.update_data(editing_bot_id=bot_id)
    await callback.message.edit_text(
        "✏️ Введи новое <b>имя</b> для бота (2–64 символа):",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(EditBotStates.editing_name)
async def process_edit_name(
    message: Message, state: FSMContext, bot: Bot, storage: Storage
) -> None:
    """
    Меняем имя управляемого бота через его токен.

    Алгоритм:
      1. getManagedBotToken(bot_id) → получаем токен
      2. Bot(token=...) → создаём инстанс
      3. set_my_name(name=...) → вызываем метод НА УПРАВЛЯЕМОМ БОТЕ
      4. session.close() → закрываем временную сессию
    """
    new_name = (message.text or "").strip()
    if len(new_name) < 2 or len(new_name) > 64:
        await message.answer(
            "❌ Имя должно быть от <b>2 до 64</b> символов. Попробуй ещё раз:",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    bot_id: int = data["editing_bot_id"]
    info = storage.get(bot_id)
    await state.clear()

    if not info:
        await message.answer("❌ Бот не найден")
        return

    try:
        managed_bot = await _get_managed_bot(bot, bot_id)
        await managed_bot.set_my_name(name=new_name)
        await managed_bot.session.close()

        # Обновляем имя в локальном хранилище
        info.first_name = new_name
        storage.add(info)

        await message.answer(
            f"✅ Имя бота @{info.username} изменено на <b>{new_name}</b>!\n\n"
            f"💡 <b>Что произошло:</b>\n"
            f"1. <code>getManagedBotToken({bot_id})</code> → получили токен\n"
            f"2. Создали <code>Bot(token=...)</code>\n"
            f"3. <code>set_my_name(name='{new_name}')</code>",
            reply_markup=bot_actions_kb(info),
        )
    except Exception as e:
        logger.exception("set_my_name failed")
        await message.answer(f"❌ Ошибка изменения имени:\n<code>{e}</code>")


# ═══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ ОПИСАНИЯ
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("edit_desc:"))
async def start_edit_description(callback: CallbackQuery, state: FSMContext) -> None:
    bot_id = int(callback.data.split(":")[1])
    await state.set_state(EditBotStates.editing_description)
    await state.update_data(editing_bot_id=bot_id)
    await callback.message.edit_text(
        "📝 Введи новое <b>описание</b> бота (до 512 символов):\n"
        "<i>Показывается в разделе «Описание» при первом запуске бота</i>",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(EditBotStates.editing_description)
async def process_edit_description(
    message: Message, state: FSMContext, bot: Bot, storage: Storage
) -> None:
    desc = (message.text or "").strip()
    if len(desc) > 512:
        await message.answer(
            "❌ Описание не должно превышать <b>512</b> символов. Попробуй ещё раз:",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    bot_id: int = data["editing_bot_id"]
    info = storage.get(bot_id)
    await state.clear()

    if not info:
        await message.answer("❌ Бот не найден")
        return

    try:
        managed_bot = await _get_managed_bot(bot, bot_id)
        await managed_bot.set_my_description(description=desc)
        await managed_bot.session.close()

        preview = desc[:80] + ("..." if len(desc) > 80 else "")
        await message.answer(
            f"✅ Описание бота @{info.username} обновлено!\n\n"
            f"<i>{preview}</i>",
            reply_markup=bot_actions_kb(info),
        )
    except Exception as e:
        logger.exception("set_my_description failed")
        await message.answer(f"❌ Ошибка:\n<code>{e}</code>")


# ═══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ КРАТКОГО ОПИСАНИЯ (about)
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("edit_short_desc:"))
async def start_edit_short_description(callback: CallbackQuery, state: FSMContext) -> None:
    bot_id = int(callback.data.split(":")[1])
    await state.set_state(EditBotStates.editing_short_description)
    await state.update_data(editing_bot_id=bot_id)
    await callback.message.edit_text(
        "📋 Введи новое <b>краткое описание</b> бота (до 120 символов):\n"
        "<i>Показывается в профиле бота и в списках поиска</i>",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(EditBotStates.editing_short_description)
async def process_edit_short_description(
    message: Message, state: FSMContext, bot: Bot, storage: Storage
) -> None:
    short_desc = (message.text or "").strip()
    if len(short_desc) > 120:
        await message.answer(
            "❌ Краткое описание не должно превышать <b>120</b> символов. Попробуй ещё раз:",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    bot_id: int = data["editing_bot_id"]
    info = storage.get(bot_id)
    await state.clear()

    if not info:
        await message.answer("❌ Бот не найден")
        return

    try:
        managed_bot = await _get_managed_bot(bot, bot_id)
        await managed_bot.set_my_short_description(short_description=short_desc)
        await managed_bot.session.close()

        await message.answer(
            f"✅ Краткое описание бота @{info.username} обновлено!\n\n"
            f"<i>{short_desc}</i>",
            reply_markup=bot_actions_kb(info),
        )
    except Exception as e:
        logger.exception("set_my_short_description failed")
        await message.answer(f"❌ Ошибка:\n<code>{e}</code>")


# ═══════════════════════════════════════════════════════════
#  ОТМЕНА FSM
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "cancel_action")
async def cancel_editing(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Редактирование отменено.")
    await callback.answer()
