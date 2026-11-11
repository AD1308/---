"""Главный цикл сбора телеметрии."""

import logging
import time
from typing import Dict, List, Optional

from .config import SystemConfig
from .sources import BaseSource
from .storage import Storage
from .trends import TrendLog
from .validator import ValueValidator
from .models import TelemetryValue, ValidationError


class Collector:
    def __init__(self, config: SystemConfig, sources: List[BaseSource],
                 storage: Storage, logger: Optional[logging.Logger] = None):
        self.config = config
        self.sources = sources
        self.storage = storage
        self.trend_log = TrendLog(config, storage)
        self.validator = ValueValidator(config)
        self.log = logger or logging.getLogger("telemetry")
        self._tick_count = 0

    def run(self, duration_seconds: Optional[float] = None) -> None:
        """Бесконечный сбор (duration_seconds=None) или сбор ограниченное время."""
        start = time.monotonic()
        self.log.info("Сбор телеметрии запущен: %d источников", len(self.sources))
        try:
            while duration_seconds is None or time.monotonic() - start < duration_seconds:
                self._tick()
                self._tick_count += 1
                self._sleep_to_next_tick()
        except KeyboardInterrupt:
            self.log.info("Остановка по Ctrl+C")
        finally:
            self.log.info("Всего тиков: %d", self._tick_count)
            self.storage.close()

    def _tick(self) -> None:
        valid: List[TelemetryValue] = []
        invalid: List[ValidationError] = []
        for source in self.sources:
            for tv in source.read():
                error = self.validator.validate(tv)
                if error is None:
                    valid.append(tv)
                else:
                    invalid.append(error)

        if valid:
            self.storage.save_telemetry(valid)
        for e in invalid:
            self.log.warning("Невалидное значение: %s/%s raw=%s причина=%s",
                             e.source_id, e.object_id, e.raw_value, e.reason)
        if invalid:
            self.storage.save_invalid(invalid)

        self.trend_log.tick(self._generate_trend_values())

        self.log.info("Тик %d: валидно=%d, невалидно=%d", self._tick_count + 1,
                      len(valid), len(invalid))

    def _generate_trend_values(self) -> Dict[str, object]:
        """Значения 20 трендов за тик (заглушка-генератор для демонстрации)."""
        import math
        ts = time.time()
        values = {}
        for i, name in enumerate(self.config.trend_names):
            if i % 2 == 0:  # чётные тренды - скалярные (синусоида + смещение)
                values[name] = round(100.0 * math.sin(ts / 60.0 + i) + i, 3)
            else:           # нечётные - булевы
                values[name] = bool(int(ts) // (30 + i) % 2)
        return values

    def _sleep_to_next_tick(self) -> None:
        elapsed = time.monotonic() % self.config.tick_seconds
        time.sleep(max(0.0, self.config.tick_seconds - elapsed))
