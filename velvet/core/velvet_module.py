"""
velvet/core/velvet_module.py

Base class for all Velvet modules.

Design goals:
- No imports from module_loader (prevents circular imports)
- Small, stable API surface
- Provides system access, logging, and safe lifecycle hooks
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class VelvetModule:
    """
    Minimal base module.

    Modules should override:
      - start()
      - stop()
      - on_event(event_name, payload)
    """

    name: str
    system: Optional[Any] = field(default=None, repr=False)

    # ----- Lifecycle -------------------------------------------------

    def attach(self, system: Any) -> None:
        """Attach the running Velvet system context to this module."""
        self.system = system

    def start(self) -> None:
        """Called after attach() when the system is starting."""
        return

    def stop(self) -> None:
        """Called during shutdown to release resources."""
        return

    # ----- Events ----------------------------------------------------

    def on_event(self, event_name: str, payload: Optional[dict] = None) -> None:
        """Event hook. Override in modules that subscribe to events."""
        return

    # ----- Helpers ---------------------------------------------------

    def log(self, msg: str) -> None:
        """Best-effort logger that won't crash if logging isn't wired yet."""
        try:
            if self.system and hasattr(self.system, "logger"):
                self.system.logger.info(f"[{self.name}] {msg}")
                return
        except Exception:
            pass
        print(f"[{self.name}] {msg}")

    def speak(self, text: str) -> None:
        """Best-effort speech helper."""
        try:
            if self.system and hasattr(self.system, "voice"):
                self.system.voice.speak(text)
                return
        except Exception:
            pass
        # Silent fallback: do nothing if voice isn't ready.
        return

    def get_config(self, key: str, default: Any = None) -> Any:
        """Fetch config from system if available."""
        if self.system and hasattr(self.system, "config"):
            try:
                return self.system.config.get(key, default)
            except Exception:
                return default
        return default
