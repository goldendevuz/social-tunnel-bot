"""
BigFatherBot — образовательный бот для изучения Managed Bots (Bot API 9.6).

Что демонстрирует этот проект:
────────────────────────────────
  • ManagedBotUpdated   — новый тип update: срабатывает при создании/обновлении
                          управляемого бота
  • getManagedBotToken  — получение токена управляемого бота
  • replaceManagedBotToken — замена токена (старый инвалидируется)
  • Deep-link создания  — t.me/newbot/{manager}/{suggested}
  • Управление через токен — создаём Bot-инстанс и вызываем set_my_name и т.д.

Требования:
────────────
  Python  >= 3.11
  aiogram >= 3.27.0  (первая версия с поддержкой Bot API 9.6)

Настройка:
──────────
  1. Создай бота через @BotFather
  2. Включи флаг can_manage_bots (через @BotFather → Bot Settings)
  3. Скопируй .env.example → .env и вставь токен
  4. pip install -r requirements.txt
  5. python main.py
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import main_router
from storage import Storage


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # MemoryStorage — для разработки.
    # В продакшене: RedisStorage из aiogram-contrib или аналог.
    dp = Dispatcher(storage=MemoryStorage())

    # Dependency Injection: передаём хранилище во все хендлеры
    storage = Storage()
    dp["storage"] = storage

    dp.include_router(main_router)

    # Информация о боте при запуске
    me = await bot.get_me()
    can_manage = getattr(me, "can_manage_bots", False)
    logger.info("Запускаю @%s (ID: %s)", me.username, me.id)
    logger.info(
        "can_manage_bots: %s%s",
        can_manage,
        "" if can_manage else "  ← нужно включить через @BotFather!",
    )

    try:
        await dp.start_polling(
            bot,
            # ВАЖНО: явно указываем "managed_bot" в allowed_updates!
            # Без этого Telegram не будет присылать ManagedBotUpdated события.
            allowed_updates=[
                "message",
                "callback_query",
                "managed_bot",   # ← Bot API 9.6: новый тип updates
            ],
        )
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
