"""
Обработчики команд /start и /help.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>Добро пожаловать в BigFatherBot!</b>\n\n"
        "Я демонстрирую новый функционал <b>Telegram Bot API 9.6</b> — "
        "<i>Managed Bots</i> (управляемые боты).\n\n"
        "Теперь один бот может создавать других ботов и управлять ими "
        "через специальные методы API!\n\n"
        "🔧 <b>Что я умею:</b>\n"
        "• Создавать новых управляемых ботов через deep-link\n"
        "• Получать токен бота: <code>getManagedBotToken</code>\n"
        "• Заменять токен: <code>replaceManagedBotToken</code>\n"
        "• Менять имя, описание через токен управляемого бота\n"
        "• Обрабатывать событие <code>ManagedBotUpdated</code>\n\n"
        "Выбери действие 👇",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📚 <b>Как работают Managed Bots (Bot API 9.6)</b>\n\n"
        "<b>1. Создание бота</b>\n"
        "Используется специальная ссылка:\n"
        "<code>t.me/newbot/{manager}/{suggested_username}</code>\n"
        "Пользователь создаёт бота через Telegram UI, "
        "а BigFatherBot получает <code>ManagedBotUpdated</code> update.\n\n"
        "<b>2. Получение токена</b>\n"
        "<code>getManagedBotToken(managed_bot_id)</code>\n"
        "Возвращает актуальный токен управляемого бота.\n\n"
        "<b>3. Замена токена</b>\n"
        "<code>replaceManagedBotToken(managed_bot_id)</code>\n"
        "Генерирует новый токен. Старый становится недействительным!\n\n"
        "<b>4. Управление настройками</b>\n"
        "Получаем токен → создаём Bot-инстанс → вызываем методы:\n"
        "• <code>set_my_name()</code>\n"
        "• <code>set_my_description()</code>\n"
        "• <code>set_my_short_description()</code>\n\n"
        "<b>5. Событие ManagedBotUpdated</b>\n"
        "Приходит когда: бот создан / токен заменён / смена владельца.\n"
        "Поля: <code>user</code> (кто сделал) + <code>bot</code> (данные бота).\n\n"
        "💡 Убедись, что у твоего бота включён флаг <b>can_manage_bots</b> "
        "через @BotFather.",
    )
