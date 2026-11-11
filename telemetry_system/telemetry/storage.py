"""Слой хранения SQLite."""

import sqlite3
import threading
from typing import List, Tuple

_SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    source_id   TEXT    NOT NULL,
    object_id   TEXT    NOT NULL,
    kind        TEXT    NOT NULL,
    value       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_telemetry_ts       ON telemetry(ts);
CREATE INDEX IF NOT EXISTS idx_telemetry_object   ON telemetry(source_id, object_id);

CREATE TABLE IF NOT EXISTS invalid_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    source_id   TEXT    NOT NULL,
    object_id   TEXT    NOT NULL,
    raw_value   TEXT    NOT NULL,
    reason      TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_invalid_ts ON invalid_log(ts);

CREATE TABLE IF NOT EXISTS trends (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    trend_id    TEXT    NOT NULL,
    value       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trends_trend_ts ON trends(trend_id, ts);
"""


class Storage:
    """Потокобезопасная обёртка над SQLite (WAL-режим)."""

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)
        self._lock = threading.Lock()

    # --- телеметрия ---
    def save_telemetry(self, batch) -> None:
        """batch: iterable[TelemetryValue] - только валидные значения."""
        rows = [(tv.timestamp, tv.source_id, tv.object_id, tv.kind,
                 _encode(tv.value)) for tv in batch]
        with self._lock, self._conn:
            self._conn.executemany(
                "INSERT INTO telemetry(ts, source_id, object_id, kind, value) "
                "VALUES (?, ?, ?, ?, ?)", rows)

    # --- невалидные ---
    def save_invalid(self, errors) -> None:
        rows = [(e.timestamp, e.source_id, e.object_id, e.raw_value, e.reason)
                for e in errors]
        with self._lock, self._conn:
            self._conn.executemany(
                "INSERT INTO invalid_log(ts, source_id, object_id, raw_value, reason) "
                "VALUES (?, ?, ?, ?, ?)", rows)

    # --- тренды ---
    def save_trend(self, trend_id: str, ts: float, value, window_size: int) -> None:
        """Сохранить точку тренда и подрезать журнал до постоянного окна видимости."""
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO trends(ts, trend_id, value) VALUES (?, ?, ?)",
                (ts, trend_id, _encode(value)))
            self._conn.execute(
                """DELETE FROM trends WHERE trend_id = ? AND id NOT IN (
                       SELECT id FROM trends WHERE trend_id = ?
                       ORDER BY ts DESC, id DESC LIMIT ?)""",
                (trend_id, trend_id, window_size))

    def get_trend_window(self, trend_id: str, limit: int = 3600) -> List[Tuple[float, object]]:
        """Вернуть окно видимости тренда (старые -> новые)."""
        cur = self._conn.execute(
            "SELECT ts, value FROM trends WHERE trend_id = ? "
            "ORDER BY ts DESC, id DESC LIMIT ?", (trend_id, limit))
        return [(ts, _decode(v)) for ts, v in reversed(cur.fetchall())]

    def close(self) -> None:
        self._conn.close()


def _encode(value) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return repr(value)


def _decode(raw: str):
    if raw in ("0", "1"):
        return raw == "1"
    try:
        return int(raw)
    except ValueError:
        return float(raw)
