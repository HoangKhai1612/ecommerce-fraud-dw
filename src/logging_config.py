
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"


def get_logger(
    name: str,
    log_file: str = "application.log",
    level: str | None = None,
) -> logging.Logger:
    """Create or retrieve a logger with console and rotating-file handlers."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(
        getattr(logging, (level or os.getenv("LOG_LEVEL", "INFO")).upper(),
                logging.INFO)
    )
    logger.propagate = False

    # Avoid duplicate handlers when the function is called repeatedly.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
