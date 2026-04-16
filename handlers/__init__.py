"""
Главный роутер — объединяет все обработчики BigFatherBot.

Порядок подключения важен:
  1. managed_events — первым, чтобы ManagedBotUpdated обрабатывался приоритетно
  2. create_bot / edit_bot — содержат cancel_action callback, поэтому
     их cancel-обработчики не должны конфликтовать с list_bots
  3. list_bots — последним среди callback-роутеров
"""
from aiogram import Router

from .create_bot import router as create_bot_router
from .edit_bot import router as edit_bot_router
from .list_bots import router as list_bots_router
from .managed_events import router as events_router
from .start import router as start_router

main_router = Router()
main_router.include_routers(
    events_router,     # ManagedBotUpdated — всегда первый
    start_router,      # /start, /help
    create_bot_router, # FSM создания бота + cancel_action
    edit_bot_router,   # FSM редактирования + cancel_action + токены
    list_bots_router,  # Список и карточки ботов
)
