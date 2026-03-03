# Velvet AI Assistant - Layer 3B Integrated

**Version**: 0.4.0  
**Status**: Layer 3B (Voice Input Light) Integrated

## What's Included

### Layer 2 Components ✅

**Memory System** (`velvet/memory.py`)
- SQLite-based event storage with WAL mode
- Thread-safe short-lived connections
- Compact JSON metadata storage
- Recent chat context retrieval

**State Management** (`velvet/state.py`)
- Device ID generation and persistence
- Mode tracking (string-based, no enums)
- First/last seen timestamps
- JSON-based settings file

**Offline Support** (`velvet/offline.py`)
- Graceful degradation when network unavailable
- Context-aware fallback messages
- No false cloud availability claims

**Path Management** (`velvet/paths.py`)
- Android-safe path resolution
- Uses App.user_data_dir
- Auto-creates directories

### Layer 3A Components ✅

**Mode Expression** (`velvet/mode_expression.py`)
- Subtle visual mode indicator (title bar only)
- Mode-aware welcome messages
- Tone hints for future API integration
- Mode change acknowledgments
- String-based, no enums
- Minimal and reversible

### Layer 3B Components ✅ NEW

**Voice Input** (`velvet/voice_input.py`)
- Android speech-to-text via plyer.stt
- Push-to-talk only (button press/release)
- No background recording or wake words
- Transcription feeds to text input (user can edit)
- Platform detection (Android only, auto-hides on desktop)
- Graceful error handling and offline support
- Minimal UI addition (mic button 🎤)

### Integration Points

**main.py** integrates Layer 2:
1. ✅ Initializes memory + state in `on_start()`
2. ✅ Uses `App.user_data_dir` for all paths
3. ✅ Logs lifecycle events (start/pause/resume)
4. ✅ Appends chat messages to memory
5. ✅ Uses offline fallback on API errors
6. ✅ All UI updates via `Clock.schedule_once()`

**Threading Model**:
- Background thread for API calls
- Main thread for all UI updates
- No blocking operations on UI thread

**Lifecycle Events Logged**:
- `app_start` - with mode and device_id
- `app_pause` - Android background
- `app_resume` - Android foreground return
- `chat` - user and velvet messages
- `error` - with fallback context

## File Structure

```
velvet_layer3a/
├── main.py                     # Kivy app with Layer 2 + 3A integration
├── buildozer.spec              # Build config (splash verified)
├── splash.png                  # 1024x1024 dark splash (#0a0a0a)
├── test_layer2.py              # Layer 2 verification tests
├── test_layer3a.py             # Layer 3A verification tests (NEW)
├── README.md                   # Integration documentation
├── LAYER3A_MODE_BEHAVIOR.md    # Mode behavior guide (NEW)
└── velvet/
    ├── __init__.py             # Package exports
    ├── api.py                  # API client (placeholder)
    ├── memory.py               # SQLite memory system
    ├── state.py                # Device state management
    ├── offline.py              # Offline fallback logic
    ├── paths.py                # Android-safe path handling
    └── mode_expression.py      # Mode expression (NEW)
```

## Data Storage

**Location**: `App.user_data_dir` (Android-safe)

**Files Created**:
- `velvet_memory.sqlite3` - Event log with WAL journal
- `velvet_settings.json` - Device state and preferences

**Database Schema**:
```sql
events (
    id INTEGER PRIMARY KEY,
    ts REAL,
    kind TEXT,           -- 'chat', 'lifecycle', 'error'
    speaker TEXT,        -- 'user', 'velvet', 'system'
    text TEXT,
    meta_json TEXT
)
```

## Code Quality Checklist

✅ SQLite paths resolve under App.user_data_dir  
✅ DB connections are short-lived (open/close per operation)  
✅ No UI mutations off main thread  
✅ Offline fallback never claims cloud access  
✅ Mode is string-based (no enums)  
✅ Splash screen preserved (#0a0a0a background)  
✅ buildozer.spec unchanged (presplash config intact)  
✅ Compact JSON storage (separators fix applied)  

## Building

```bash
# Install buildozer
pip install buildozer

# Build APK
buildozer android debug

# Deploy to device
buildozer android deploy run logcat
```

## API Integration (TODO)

The `velvet/api.py` module is currently a placeholder. To complete:

1. Implement `chat()` function with actual API endpoint
2. Handle authentication if required
3. Add retry logic for transient failures
4. Return parsed response text

Example signature:
```python
def chat(user_text: str, 
         recent_context: List[Tuple[str, str]] = None,
         mode: str = "Normal") -> str:
    # Your API call here
    pass
```

## Testing on Android

**Verify Paths**:
```python
from velvet.paths import db_path, settings_path
print(db_path(app.user_data_dir))
# Should print: /data/data/org.velvet.velvet/files/velvet_memory.sqlite3
```

**Check Memory**:
```python
from velvet.memory import VelvetMemory
mem = VelvetMemory(db_path(app.user_data_dir))
events = mem.tail(limit=10)
for e in events:
    print(f"{e.kind}: {e.speaker} - {e.text[:50]}")
```

**Verify State**:
```python
from velvet.state import load_state
state = load_state(settings_path(app.user_data_dir))
print(f"Device: {state.device_id}")
print(f"Mode: {state.mode}")
```

## Micro-Fix Applied

**JSON Compact Storage** (from code check):
```python
# Before: json.dumps(meta, ensure_ascii=False)
# After:  json.dumps(meta, ensure_ascii=False, separators=(',', ':'))
```
This reduces storage overhead for metadata in the events table.

## Next Steps

### Layer 3A: Mode Expression Testing

**Test Mode Changes**:
```
# In the app chat, type:
/mode Cautious   # Switch to cautious mode
/mode Degraded   # Switch to degraded mode
/mode Debug      # Switch to debug mode
/mode Normal     # Back to normal
```

**Observe**:
- Title bar updates to show mode
- Welcome message changes based on mode
- Acknowledgment appears when mode switches

**See**: `LAYER3A_MODE_BEHAVIOR.md` for detailed behavior guide

### API Implementation (Your Side)

Complete `velvet/api.py`:

```python
def chat(user_text: str, 
         recent_context: List[Tuple[str, str]] = None,
         mode: str = "Normal") -> str:
    # 1. Format request with context
    # 2. Call your API endpoint
    # 3. Parse response
    # 4. Return text
    # 5. Raise exception on failure (triggers offline fallback)
    
    # Layer 3A: Optionally use mode for tone
    from velvet.mode_expression import get_tone_hint
    tone = get_tone_hint(mode)  # "measured", "constrained", "verbose", or ""
    # Incorporate 'tone' into system prompt or request if desired
    
    pass
```

---

**Notes**:
- No analytics or tracking
- No cloud dependencies beyond API calls
- No animations or UI redesign
- Splash screen final and locked
- Mode expression is minimal and reversible
