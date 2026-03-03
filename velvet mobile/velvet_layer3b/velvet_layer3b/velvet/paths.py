from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_user_data_dir(app_user_data_dir: Optional[str]) -> Path:
    if not app_user_data_dir:
        base = Path(os.getcwd()) / ".velvet_user_data"
    else:
        base = Path(app_user_data_dir)
    return ensure_dir(base)

def db_path(app_user_data_dir: Optional[str]) -> Path:
    return get_user_data_dir(app_user_data_dir) / "velvet_memory.sqlite3"

def settings_path(app_user_data_dir: Optional[str]) -> Path:
    return get_user_data_dir(app_user_data_dir) / "velvet_settings.json"
