"""
Обработчик события ManagedBotUpdated — ключевого нового update типа Bot API 9.6.

Когда приходит этот update:
─────────────────────────────
  • Пользователь создал нового управляемого бота (через deep-link)
  • Токен управляемого бота был заменён (replaceManagedBotToken)
  • Право управления ботом было передано другому пользователю

Структура ManagedBotUpdated:
─────────────────────────────
  user: User  — пользователь, который создал или изменил бота
  bot:  User  — данные об управляемом боте (is_bot=True)
               токен можно получить через getManagedBotToken(bot.id)

Как это регистрируется в aiogram 3:
─────────────────────────────────────
  @router.managed_bot()
  async def handler(managed_bot: ManagedBotUpdated, ...):
      ...

В allowed_updates нужно явно добавить "managed_bot"!
"""
import logging
from datetime import datetime

from aiogram import Bot, Router
from aiogram.types import ManagedBotUpdated

from keyboards import bot_actions_kb
from storage import ManagedBotInfo, Storage

router = Router()
logger = logging.getLogger(__name__)


@router.managed_bot()
async def on_managed_bot_updated(
    managed_bot: ManagedBotUpdated,
    bot: Bot,
    storage: Storage,
) -> None:
    """
    Обрабатываем событие ManagedBotUpdated.

    managed_bot.user — пользователь, совершивший действие
    managed_bot.bot  — объект User, описывающий управляемого бота
    """
    creator = managed_bot.user
    new_bot = managed_bot.bot

    logger.info(
        "ManagedBotUpdated: creator=%s (@%s), bot=%s (@%s)",
        creator.id,
        creator.username,
        new_bot.id,
        new_bot.username,
    )

    # Проверяем: это новый бот или обновление существующего?
    existing = storage.get(new_bot.id)
    is_new = existing is None

    # Сохраняем / обновляем информацию в хранилище
    info = ManagedBotInfo(
        bot_id=new_bot.id,
        username=new_bot.username or "",
        first_name=new_bot.first_name,
        owner_id=creator.id,
        # Сохраняем оригинальную дату создания, если бот уже есть
        created_at=existing.created_at if existing else datetime.now().isoformat(),
    )
    storage.add(info)

    # ──── Уведомляем создателя ────
    if is_new:
        text = (
            f"🎉 <b>Управляемый бот успешно создан!</b>\n\n"
            f"🤖 Имя: <b>{new_bot.first_name}</b>\n"
            f"👤 Username: @{new_bot.username}\n"
            f"🆔 ID: <code>{new_bot.id}</code>\n\n"
            f"Бот добавлен в твой список. Открой <b>📋 Мои боты</b> для управления.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>Что произошло технически:</b>\n"
            f"BigFatherBot получил update типа <code>ManagedBotUpdated</code> — "
            f"новый тип событий из <b>Bot API 9.6</b>.\n\n"
            f"Структура события:\n"
            f"<code>managed_bot.user.id = {creator.id}</code>\n"
            f"<code>managed_bot.bot.id  = {new_bot.id}</code>"
        )
    else:
        text = (
            f"🔄 <b>Управляемый бот обновлён!</b>\n\n"
            f"🤖 Бот: @{new_bot.username} (ID: <code>{new_bot.id}</code>)\n\n"
            f"Информация обновлена в хранилище.\n\n"
            f"💡 <code>ManagedBotUpdated</code> приходит при:\n"
            f"• Создании бота\n"
            f"• Замене токена (<code>replaceManagedBotToken</code>)\n"
            f"• Смене владельца"
        )

    try:
        await bot.send_message(
            chat_id=creator.id,
            text=text,
            reply_markup=bot_actions_kb(info) if is_new else None,
        )
    except Exception:
        # Пользователь мог не запустить бота — просто логируем
        logger.warning("Не удалось уведомить пользователя %s", creator.id)
