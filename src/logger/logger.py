import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import AppConfig

#config object
config=AppConfig()

def setup_logger(name: str = "Islam-QA") -> logging.Logger:
    logger = logging.getLogger(name)

    # Prevent duplicate logs
    if logger.handlers:
        return logger

    logger.setLevel(config.LOG_LEVEL)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )

    # ───── Console handler ─────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # ───── File handler ─────
    log_path = Path(config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
