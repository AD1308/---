"""Источники телеметрии.

Для демонстрации работы системы реализован SimulatedSource:
- каталог до 1000 объектов на источник;
- раз в секунду отдаёт случайные 100-600 объектов;
- значения скалярные (float) или булевы;
- редко (invalid_probability) порождает невалидные значения,
  чтобы продемонстрировать ветку логирования ошибок.

Для подключения реальных источников реализуйте BaseSource.read().
"""

import random
import time
from typing import List

from .config import SourceConfig, SystemConfig
from .models import BOOLEAN, SCALAR, TelemetryValue


class BaseSource:
    """Интерфейс источника телеметрии."""

    def __init__(self, config: SourceConfig):
        self.config = config
        self.source_id = config.source_id

    def read(self) -> List[TelemetryValue]:
        """Вернуть пачку значений за один тик. Один объект - не более одного раза."""
        raise NotImplementedError


class SimulatedSource(BaseSource):
    def __init__(self, config: SourceConfig, system_config: SystemConfig, rng: random.Random):
        super().__init__(config)
        self._rng = rng
        self._invalid_probability = system_config.invalid_probability
        # Каталог объектов источника: до 1000 объектов, половина скалярных, половина булевых
        half = config.max_objects // 2
        self._catalog = (
            [(f"{self.source_id}.S{i:04d}", SCALAR) for i in range(half)]
            + [(f"{self.source_id}.B{i:04d}", BOOLEAN) for i in range(config.max_objects - half)]
        )

    def read(self) -> List[TelemetryValue]:
        ts = time.time()
        n = self._rng.randint(self.config.min_per_tick, self.config.max_per_tick)
        batch = self._rng.sample(self._catalog, n)
        return [TelemetryValue(self.source_id, oid, kind,
                               self._make_value(kind), ts) for oid, kind in batch]

    def _make_value(self, kind: str):
        if self._rng.random() < self._invalid_probability:
            return self._make_invalid(kind)
        if kind == BOOLEAN:
            return bool(self._rng.getrandbits(1))
        return round(self._rng.uniform(-500.0, 500.0), 3)

    def _make_invalid(self, kind: str):
        """Породить заведомо невалидное значение."""
        choice = self._rng.randrange(4)
        if choice == 0:
            return "not_a_number"          # неверный тип
        if choice == 1:
            return float("nan")            # NaN
        if choice == 2:
            return float("inf")            # бесконечность
        return 10 ** 9 if kind == SCALAR else 42  # вне диапазона / не bool


def build_default_sources(system_config: SystemConfig) -> List[BaseSource]:
    rng = random.Random()
    return [SimulatedSource(cfg, system_config, rng) for cfg in system_config.sources]
