"""Structured logging configuration."""

import logging
import sys
from app.core.config import settings


def setup_logging():
    """Configure application-wide logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "multipart"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
    
    logging.getLogger(__name__).info("Logging configured successfully")
