from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

DEFAULT_MODE = "Normal"

@dataclass
class VelvetState:
    device_id: str
    mode: str
    first_seen_ts: float
    last_seen_ts: float

def _now() -> float:
    return time.time()

def load_state(settings_file: Path) -> VelvetState:
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    else:
        data = {}

    st = VelvetState(
        device_id=data.get("device_id") or str(uuid.uuid4()),
        mode=data.get("mode") or DEFAULT_MODE,
        first_seen_ts=data.get("first_seen_ts") or _now(),
        last_seen_ts=data.get("last_seen_ts") or _now(),
    )
    save_state(settings_file, st)
    return st

def save_state(settings_file: Path, st: VelvetState) -> None:
    payload: Dict[str, Any] = {
        "device_id": st.device_id,
        "mode": st.mode,
        "first_seen_ts": st.first_seen_ts,
        "last_seen_ts": st.last_seen_ts,
    }
    settings_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def set_mode(settings_file: Path, st: VelvetState, new_mode: str) -> VelvetState:
    st.mode = new_mode
    st.last_seen_ts = _now()
    save_state(settings_file, st)
    return st

def touch_seen(settings_file: Path, st: VelvetState) -> VelvetState:
    st.last_seen_ts = _now()
    save_state(settings_file, st)
    return st
