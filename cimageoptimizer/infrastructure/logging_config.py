"""Structured logging setup for the application."""

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configures root logging once, at application startup."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
