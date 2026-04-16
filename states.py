"""
FSM-состояния для многошаговых диалогов BigFatherBot.
"""
from aiogram.fsm.state import State, StatesGroup


class CreateBotStates(StatesGroup):
    """Состояния при создании нового управляемого бота."""
    waiting_for_name = State()      # Ожидаем отображаемое имя
    waiting_for_username = State()  # Ожидаем username (должен кончаться на 'bot')


class EditBotStates(StatesGroup):
    """Состояния при редактировании настроек управляемого бота."""
    editing_name = State()              # Ждём новое имя
    editing_description = State()       # Ждём новое описание (до 512 символов)
    editing_short_description = State() # Ждём новое краткое описание (до 120 символов)
