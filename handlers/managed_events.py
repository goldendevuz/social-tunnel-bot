"""
handlers/managed_events.py
"""
import logging
from datetime import datetime

from aiogram import Bot, Router
from aiogram.types import ManagedBotUpdated, Update

from keyboards import bot_actions_kb
from storage import ManagedBotInfo, Storage
from child_bot_runner import launch_child_bot

router = Router()
logger = logging.getLogger(__name__)


@router.managed_bot()
async def on_managed_bot_updated(
    managed_bot: ManagedBotUpdated,
    bot: Bot,
    storage: Storage,
    **kwargs,
) -> None:
    creator = managed_bot.user

    # kwargs ichida update bor
    update = kwargs.get("event_update")
    raw = update.model_dump() if update else {}
    raw_bot = raw.get("managed_bot", {}).get("bot_user", {})
    child_bot_id       = raw_bot.get("id")
    child_bot_username = raw_bot.get("username") or str(child_bot_id)
    child_bot_name     = raw_bot.get("first_name") or child_bot_username

    logger.info("kwargs keys: %s", list(kwargs.keys()))
    logger.info("Raw managed_bot.bot: %s", raw_bot)
    logger.info(
        "ManagedBotUpdated: creator=%s (@%s), child_bot_id=%s (@%s)",
        creator.id, creator.username,
        child_bot_id, child_bot_username,
    )

    if not child_bot_id:
        logger.error("child_bot_id topilmadi, raw: %s", raw)
        return

    existing = storage.get(child_bot_id)
    is_new   = existing is None

    info = ManagedBotInfo(
        bot_id     = child_bot_id,
        username   = child_bot_username,
        first_name = child_bot_name,
        owner_id   = creator.id,
        created_at = existing.created_at if existing else datetime.now().isoformat(),
    )

    # ──── Child bot tokenini olib ishga tushirish ────────────────────────────
    try:
        result = await bot.get_managed_bot_token(user_id=child_bot_id)
        child_token = result.token if hasattr(result, 'token') else str(result)

        # Token orqali aniq ma'lumot olamiz
        tmp_bot = Bot(token=child_token)
        me = await tmp_bot.get_me()
        await tmp_bot.session.close()

        child_bot_username = me.username or child_bot_username
        child_bot_name     = me.first_name or child_bot_name

        info.username   = child_bot_username
        info.first_name = child_bot_name
        info.token      = child_token
        storage.add(info)

        from config import TELEGRAM_API_BASE

        await launch_child_bot(
            child_bot_id      = child_bot_id,
            child_token       = child_token,
            username          = child_bot_username,
            telegram_api_base = TELEGRAM_API_BASE,
        )
        launch_ok = True

    except Exception as exc:
        logger.error("Child bot ishga tushmadi: %s", exc)
        storage.add(info)
        launch_ok = False
    # ─────────────────────────────────────────────────────────────────────────

    if is_new:
        status = "✅ Bot ishga tushdi!" if launch_ok else "⚠️ Bot yaratildi, lekin ishga tushmadi"
        text = (
            f"🎉 <b>Yangi bot yaratildi!</b>\n\n"
            f"🤖 Nomi: <b>{child_bot_name}</b>\n"
            f"👤 Username: @{child_bot_username}\n"
            f"🆔 ID: <code>{child_bot_id}</code>\n\n"
            f"{status}\n\n"
            f"📥 Botingizga o'ting va video havolasini yuboring!"
        )
    else:
        text = (
            f"🔄 <b>Bot yangilandi!</b>\n\n"
            f"🤖 @{child_bot_username} (ID: <code>{child_bot_id}</code>)\n"
            f"Ma'lumotlar yangilandi."
        )

    try:
        await bot.send_message(
            chat_id      = creator.id,
            text         = text,
            reply_markup = bot_actions_kb(info) if is_new else None,
        )
    except Exception:
        logger.warning("Foydalanuvchi %s ga xabar yuborib bo'lmadi", creator.id)
