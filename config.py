"""
Конфигурация BigFatherBot.
Токен загружается из переменной окружения BOT_TOKEN (файл .env).
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env da yo'q")

# ← QO'SHILDI: saverapi-bot uchun kerakli o'zgaruvchilar
SAVER_API_KEY: str = os.environ.get("SAVER_API_KEY", "")
TELEGRAM_API_BASE: str | None = os.environ.get("TELEGRAM_API_BASE", None)

if not SAVER_API_KEY:
    raise ValueError("SAVER_API_KEY .env da yo'q")
