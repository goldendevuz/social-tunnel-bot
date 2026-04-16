"""
FSM-обработчики для создания нового управляемого бота.

Поток:
  1. Пользователь нажимает «🤖 Создать бота»
  2. Бот спрашивает желаемое отображаемое имя
  3. Бот спрашивает желаемый username
  4. Генерируем deep-link: t.me/newbot/{manager}/{suggested}?name={name}
  5. Пользователь переходит по ссылке и создаёт бота в Telegram
  6. BigFatherBot получает ManagedBotUpdated → обработчик в managed_events.py

Bot API 9.6: ссылка t.me/newbot/{manager_username}/{suggested_username}
привязывает создаваемого бота к менеджер-боту автоматически.
"""
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards import cancel_kb, main_menu_kb
from states import CreateBotStates

router = Router()


def _make_deep_link(manager_username: str, suggested_username: str, suggested_name: str) -> str:
    """
    Формируем ссылку для создания управляемого бота.

    Bot API 9.6 добавил поддержку ссылок формата:
        https://t.me/newbot/{manager_username}/{suggested_username}?name={suggested_name}

    После перехода по такой ссылке Telegram предложит создать бота,
    который будет сразу привязан к {manager_username} как управляемый.
    """
    url = f"https://t.me/newbot/{manager_username}/{suggested_username}"
    if suggested_name:
        # URL-encode имя вручную (простые символы не требуют encode)
        url += f"?name={suggested_name.replace(' ', '%20')}"
    return url


# ─────────────────── Точка входа ───────────────────

@router.message(F.text == "🤖 Создать бота")
async def start_create_from_menu(message: Message, state: FSMContext) -> None:
    await _ask_for_name(message, state)


@router.callback_query(F.data == "create_bot")
async def start_create_from_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await _ask_for_name(callback.message, state)


async def _ask_for_name(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateBotStates.waiting_for_name)
    await message.answer(
        "🤖 <b>Создание управляемого бота</b>\n\n"
        "Шаг <b>1/2</b> — Введи <b>отображаемое имя</b> нового бота\n"
        "Например: <i>Weather Helper</i>",
        reply_markup=cancel_kb(),
    )


# ─────────────────── Шаг 1: имя бота ───────────────────

@router.message(CreateBotStates.waiting_for_name)
async def process_bot_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip() if message.text else ""

    if len(name) < 2 or len(name) > 64:
        await message.answer(
            "❌ Имя должно быть от <b>2 до 64</b> символов. Попробуй ещё раз:",
            reply_markup=cancel_kb(),
        )
        return

    await state.update_data(bot_name=name)
    await state.set_state(CreateBotStates.waiting_for_username)

    await message.answer(
        f"✅ Имя: <b>{name}</b>\n\n"
        "Шаг <b>2/2</b> — Введи желаемый <b>username</b> для нового бота:\n"
        "• Только латинские буквы, цифры и <code>_</code>\n"
        "• Должен заканчиваться на <code>bot</code>\n"
        "Например: <i>weather_helper_bot</i>",
        reply_markup=cancel_kb(),
    )


# ─────────────────── Шаг 2: username → генерируем ссылку ───────────────────

@router.message(CreateBotStates.waiting_for_username)
async def process_bot_username(message: Message, state: FSMContext, bot: Bot) -> None:
    username = (message.text or "").strip().lstrip("@")

    if not username.lower().endswith("bot"):
        await message.answer(
            "❌ Username должен заканчиваться на <code>bot</code>. Попробуй ещё раз:",
            reply_markup=cancel_kb(),
        )
        return

    data = await state.get_data()
    bot_name: str = data["bot_name"]
    await state.clear()

    # Получаем username текущего (менеджер) бота
    me = await bot.get_me()
    manager_username: str = me.username or ""

    # Генерируем deep-link (Bot API 9.6)
    create_url = _make_deep_link(
        manager_username=manager_username,
        suggested_username=username,
        suggested_name=bot_name,
    )

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🚀 Перейти и создать бота", url=create_url)
    )

    await message.answer(
        f"🎉 <b>Всё готово!</b>\n\n"
        f"📌 Имя: <b>{bot_name}</b>\n"
        f"📌 Username: <code>@{username}</code>\n\n"
        f"Нажми кнопку ниже — Telegram откроет форму создания бота.\n"
        f"После создания я автоматически получу событие "
        f"<b>ManagedBotUpdated</b> и уведомлю тебя.\n\n"
        f"💡 <i>Ссылка использует новый формат Bot API 9.6:</i>\n"
        f"<code>t.me/newbot/{manager_username}/{username}</code>",
        reply_markup=builder.as_markup(),
    )

    await message.answer(
        "⏳ Жду, пока ты создашь бота...",
        reply_markup=main_menu_kb(),
    )


# ─────────────────── Отмена FSM ───────────────────

@router.callback_query(F.data == "cancel_action")
async def cancel_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()
