"""
child_bot_runner.py — social-tunnel-bot/ papkasiga qo'ying.

Muammo: saverapi-bot/handlers/ va social-tunnel-bot/handlers/ nomlar to'qnashadi.
Yechim: importlib bilan har bir modulni to'liq yo'l orqali, noyob nom bilan yuklaymiz.
"""

import asyncio
import importlib.util
import logging
import os
import sys
from typing import Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

logger = logging.getLogger(__name__)

# Faol child botlar: {child_bot_id: (Bot, asyncio.Task)}
_running_bots: Dict[int, tuple] = {}

# saverapi-bot modullar bir marta yuklanadi
_saverapi_modules_loaded = False


def _get_saverapi_path() -> str:
    """saverapi-bot papkasining mutlaq yo'lini qaytaradi."""
    current = os.path.dirname(os.path.abspath(__file__))
    # social-tunnel-bot/ yonida saverapi-bot/ bo'lishi kerak
    candidate = os.path.normpath(os.path.join(current, "..", "saverapi-bot"))
    if os.path.isdir(candidate):
        return candidate
    raise FileNotFoundError(
        f"saverapi-bot topilmadi: {candidate}\n"
        "Loyihalar yonma-yon bo'lishi kerak:\n"
        "  botsoft/social-tunnel-bot/\n"
        "  botsoft/saverapi-bot/"
    )


def _load_module(module_name: str, file_path: str):
    """
    Modulni to'liq yo'l orqali yuklab sys.modules ga qo'shadi.
    Agar allaqachon yuklangan bo'lsa, qaytadan yuklamaydi.
    """
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Modul topilmadi: {file_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_saverapi_modules():
    """
    saverapi-bot modullarini noyob nomlar bilan yuklaymiz.
    Bu social-tunnel-bot/handlers/ bilan to'qnashuvni oldini oladi.
    """
    global _saverapi_modules_loaded
    if _saverapi_modules_loaded:
        return

    p = _get_saverapi_path()
    logger.info("saverapi-bot yo'li: %s", p)

    # SAVER_API_KEY env da bo'lishi kerak (social-tunnel-bot/.env da)
    saver_key = os.getenv("SAVER_API_KEY", "")
    if not saver_key:
        raise ValueError("SAVER_API_KEY .env da yo'q — social-tunnel-bot/.env ga qo'shing")

    # BOT_TOKEN saverapi config.py uchun kerak (validation o'tishi uchun)
    # social-tunnel-bot/.env dagi BOT_TOKEN ishlatiladi — bu normalda o'rnatilgan
    # Agar yo'q bo'lsa vaqtinchalik o'rnatamiz
    if not os.getenv("BOT_TOKEN"):
        os.environ["BOT_TOKEN"] = "placeholder"

    # 1. saverapi config — "saver_config" nomi bilan
    # 1. saverapi config
    _load_module("saver_config", f"{p}/config.py")

    # ← shu qatorni shu yerga ko'chiring (utils yuklanishidan OLDIN)
    sys.modules["config"] = sys.modules["saver_config"]

    # 2. utils package
    _load_module("saver_utils",           f"{p}/utils/__init__.py")
    _load_module("saver_utils.youtube",   f"{p}/utils/youtube.py")
    _load_module("saver_utils.instagram", f"{p}/utils/instagram.py")

    sys.modules["utils"] = sys.modules["saver_utils"]
    sys.modules["utils.youtube"] = sys.modules["saver_utils.youtube"]
    sys.modules["utils.instagram"] = sys.modules["saver_utils.instagram"]

    # 3. handlers
    _load_module("saver_handlers_start",     f"{p}/handlers/start.py")
    _load_module("saver_handlers_youtube",   f"{p}/handlers/youtube.py")
    _load_module("saver_handlers_instagram", f"{p}/handlers/instagram.py")

    # 4. config aliasini tiklaymiz
    if original_config is not None:
        sys.modules["config"] = original_config
    elif "config" in sys.modules:
        del sys.modules["config"]

    _saverapi_modules_loaded = True
    logger.info("saverapi-bot modullari muvaffaqiyatli yuklandi")


def _build_child_dispatcher() -> Dispatcher:
    """saverapi-bot handlerlarini ishlatib yangi Dispatcher yaratadi."""
    _load_saverapi_modules()

    saver_start     = sys.modules["saver_handlers_start"]
    saver_youtube   = sys.modules["saver_handlers_youtube"]
    saver_instagram = sys.modules["saver_handlers_instagram"]

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(saver_start.router)
    dp.include_router(saver_youtube.router)
    dp.include_router(saver_instagram.router)
    return dp


async def launch_child_bot(
    child_bot_id: int,
    child_token: str,
    username: str,
    telegram_api_base: str | None = None,
) -> None:
    """Child botni ishga tushiradi."""
    if child_bot_id in _running_bots:
        logger.warning("Child bot @%s allaqachon ishlamoqda", username)
        return

    if telegram_api_base:
        session = AiohttpSession(
            api=TelegramAPIServer.from_base(telegram_api_base)
        )
    else:
        session = AiohttpSession()

    child_bot = Bot(
        token=child_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = _build_child_dispatcher()

    async def _poll():
        try:
            logger.info("Child bot @%s polling boshlanmoqda...", username)
            await dp.start_polling(child_bot, handle_signals=False)
        except asyncio.CancelledError:
            logger.info("Child bot @%s to'xtatildi", username)
        except Exception as exc:
            logger.error("Child bot @%s xatosi: %s", username, exc, exc_info=True)
        finally:
            await child_bot.session.close()
            _running_bots.pop(child_bot_id, None)

    task = asyncio.create_task(_poll(), name=f"child_{username}")
    _running_bots[child_bot_id] = (child_bot, task)
    logger.info("Child bot @%s ishga tushdi (ID: %s)", username, child_bot_id)


async def stop_child_bot(child_bot_id: int) -> bool:
    """Child botni to'xtatadi."""
    entry = _running_bots.get(child_bot_id)
    if not entry:
        return False
    _, task = entry
    task.cancel()
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=5)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    logger.info("Child bot ID=%s to'xtatildi", child_bot_id)
    return True


def is_running(child_bot_id: int) -> bool:
    return child_bot_id in _running_bots
