"""Конфигурация системы сбора телеметрии."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceConfig:
    source_id: str
    max_objects: int = 1000          # каталог объектов источника (до 1000)
    min_per_tick: int = 100          # минимум объектов за тик
    max_per_tick: int = 600          # максимум объектов за тик


@dataclass(frozen=True)
class SystemConfig:
    tick_seconds: float = 1.0
    sources: tuple = (
        SourceConfig("SRC_1"),
        SourceConfig("SRC_2"),
        SourceConfig("SRC_3"),
        SourceConfig("SRC_4"),
    )
    trend_names: tuple = tuple(f"TREND_{i:02d}" for i in range(1, 21))  # 20 трендов
    trend_window_size: int = 3600          # постоянное окно видимости журнала трендов
    # Допустимый диапазон скалярных значений (меняется под предметную область)
    scalar_min: float = -1_000_000.0
    scalar_max: float = 1_000_000.0
    invalid_probability: float = 0.005     # доля "битых" значений от симулятора (демо)
    db_path: str = "telemetry.db"
    log_dir: str = "logs"
