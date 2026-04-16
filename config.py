"""
Конфигурация BigFatherBot.
Токен загружается из переменной окружения BOT_TOKEN (файл .env).
"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise ValueError(
        "Переменная окружения BOT_TOKEN не задана. "
        "Создай файл .env по образцу .env.example"
    )
