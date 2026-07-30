"""Loads and saves user-editable application settings (settings.json)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

APP_SETTINGS_DIRNAME = "CImageOptimizer"
SETTINGS_FILENAME = "settings.json"


def get_settings_path() -> Path:
    """Returns the per-user settings file path (%APPDATA% on Windows)."""
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_SETTINGS_DIRNAME / SETTINGS_FILENAME


def load_settings(path: Optional[Path] = None) -> dict[str, Any]:
    """Reads settings.json, returning an empty dict if missing or invalid."""
    path = path or get_settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Ignoring unreadable settings file %s: %s", path, exc)
        return {}


def save_settings(data: dict[str, Any], path: Optional[Path] = None) -> None:
    """Writes settings.json, creating its parent directory if needed."""
    path = path or get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
