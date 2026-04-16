"""
Простое JSON-хранилище для информации об управляемых ботах.

В продакшене стоит заменить на SQLite (через aiosqlite) или PostgreSQL.
Здесь используем JSON-файл ради простоты и понятности кода.
"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

STORAGE_FILE = "managed_bots.json"


@dataclass
class ManagedBotInfo:
    """Данные об управляемом боте, которые мы храним локально."""
    bot_id: int
    username: str
    first_name: str
    owner_id: int          # Telegram ID пользователя, создавшего бота
    created_at: str = ""   # ISO-формат datetime

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class Storage:
    """Менеджер JSON-хранилища управляемых ботов."""

    def __init__(self) -> None:
        self._bots: dict[int, ManagedBotInfo] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, encoding="utf-8") as f:
                raw: dict = json.load(f)
            self._bots = {
                int(k): ManagedBotInfo(**v) for k, v in raw.items()
            }

    def _save(self) -> None:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {str(k): asdict(v) for k, v in self._bots.items()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def add(self, bot: ManagedBotInfo) -> None:
        """Добавить или обновить запись о боте."""
        self._bots[bot.bot_id] = bot
        self._save()

    def get(self, bot_id: int) -> Optional[ManagedBotInfo]:
        """Получить данные о конкретном боте по его ID."""
        return self._bots.get(bot_id)

    def all_by_owner(self, owner_id: int) -> list[ManagedBotInfo]:
        """Все боты конкретного пользователя."""
        return [b for b in self._bots.values() if b.owner_id == owner_id]

    def remove(self, bot_id: int) -> bool:
        """Удалить бота из хранилища."""
        if bot_id in self._bots:
            del self._bots[bot_id]
            self._save()
            return True
        return False
