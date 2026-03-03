"""
Velvet AI Assistant - Core Package
Layer 2: Memory + State + Presence + Offline
Layer 3A: Mode Expression (Light)
Layer 3B: Voice Input (Light)
"""

from . import api
from .memory import VelvetMemory, MemoryEvent
from .state import VelvetState, load_state, save_state, set_mode, touch_seen
from .offline import offline_fallback
from .paths import db_path, settings_path, get_user_data_dir
from . import mode_expression
from . import voice_input

__all__ = [
    'api',
    'VelvetMemory',
    'MemoryEvent',
    'VelvetState',
    'load_state',
    'save_state',
    'set_mode',
    'touch_seen',
    'offline_fallback',
    'db_path',
    'settings_path',
    'get_user_data_dir',
    'mode_expression',
    'voice_input',
]
