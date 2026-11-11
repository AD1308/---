"""Валидация значений телеметрии."""

import math
from typing import Optional

from .config import SystemConfig
from .models import BOOLEAN, SCALAR, TelemetryValue, ValidationError


class ValueValidator:
    """Проверяет значение на соответствие типу и диапазону."""

    def __init__(self, config: SystemConfig):
        self._scalar_min = config.scalar_min
        self._scalar_max = config.scalar_max

    def validate(self, tv: TelemetryValue) -> Optional[ValidationError]:
        """Вернуть None, если значение валидно, иначе - описание ошибки."""
        value = tv.value
        if tv.kind == BOOLEAN:
            if not isinstance(value, bool):
                return self._error(tv, f"ожидался bool, получено {type(value).__name__}")
            return None
        if tv.kind == SCALAR:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return self._error(tv, f"ожидалось число, получено {type(value).__name__}")
            if not math.isfinite(value):
                return self._error(tv, "значение не является конечным числом (NaN/Inf)")
            if not (self._scalar_min <= value <= self._scalar_max):
                return self._error(tv, f"значение вне диапазона [{self._scalar_min}; {self._scalar_max}]")
            return None
        return self._error(tv, f"неизвестный тип значения: {tv.kind!r}")

    @staticmethod
    def _error(tv: TelemetryValue, reason: str) -> ValidationError:
        return ValidationError(
            source_id=tv.source_id,
            object_id=tv.object_id,
            raw_value=repr(tv.value),
            reason=reason,
            timestamp=tv.timestamp,
        )
