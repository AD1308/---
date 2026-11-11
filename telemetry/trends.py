"""Журнал трендов с постоянным окном видимости (3600 элементов)."""

import time
from collections import deque
from typing import Dict, List, Tuple

from .config import SystemConfig
from .storage import Storage


class TrendLog:
    """
    Ведёт журнал 20 предопределённых трендов.

    - каждый тик все тренды пишутся в SQLite;
    - в БД и в памяти поддерживается постоянное окно видимости
      window_size элементов на тренд (старое удаляется).
    """

    def __init__(self, config: SystemConfig, storage: Storage):
        self._config = config
        self._storage = storage
        self._windows: Dict[str, deque] = {
            name: deque(maxlen=config.trend_window_size) for name in config.trend_names
        }

    def tick(self, values: Dict[str, object]) -> None:
        """Записать значения трендов за тик и обновить окно видимости."""
        ts = time.time()
        for name in self._config.trend_names:
            value = values[name]
            self._storage.save_trend(name, ts, value, self._config.trend_window_size)
            window = self._windows[name]
            window.append((ts, value))

    def window(self, trend_id: str) -> List[Tuple[float, object]]:
        """Окно видимости тренда (старые -> новые), до window_size элементов."""
        return list(self._windows[trend_id])

    @property
    def trend_names(self):
        return self._config.trend_names
