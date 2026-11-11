"""Модели данных телеметрии."""

from dataclasses import dataclass
from typing import Union

SCALAR = "scalar"
BOOLEAN = "bool"

Value = Union[int, float, bool]


@dataclass(frozen=True)
class TelemetryValue:
    """Одно значение от одного объекта одного источника."""
    source_id: str
    object_id: str
    kind: str            # SCALAR или BOOLEAN
    value: Value
    timestamp: float     # unix-time, секунды


@dataclass(frozen=True)
class ValidationError:
    """Причина отклонения значения."""
    source_id: str
    object_id: str
    raw_value: str       # значение как пришло (repr)
    reason: str
    timestamp: float
