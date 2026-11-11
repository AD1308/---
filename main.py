#!/usr/bin/env python3
"""Точка входа системы сбора телеметрии."""

import argparse
import logging
import os

from telemetry.collector import Collector
from telemetry.config import SystemConfig
from telemetry.sources import build_default_sources
from telemetry.storage import Storage


def setup_logger(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("telemetry")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    fh = logging.FileHandler(os.path.join(log_dir, "telemetry.log"), encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


def main() -> None:
    parser = argparse.ArgumentParser(description="Система сбора телеметрии")
    parser.add_argument("--duration", type=float, default=None,
                        help="время работы в секундах (по умолчанию - бесконечно)")
    parser.add_argument("--db", type=str, default=None, help="путь к БД SQLite")
    args = parser.parse_args()

    config = SystemConfig(db_path=args.db or SystemConfig.db_path)
    logger = setup_logger(config.log_dir)
    storage = Storage(config.db_path)
    sources = build_default_sources(config)

    Collector(config, sources, storage, logger).run(duration_seconds=args.duration)


if __name__ == "__main__":
    main()
