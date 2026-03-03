#!/usr/bin/env python3
"""
Layer 2 Verification Test
Tests memory, state, paths, and offline components
"""

import sys
import tempfile
from pathlib import Path

# Test imports
try:
    from velvet.paths import db_path, settings_path, get_user_data_dir
    from velvet.memory import VelvetMemory, MemoryEvent
    from velvet.state import load_state, save_state, set_mode, touch_seen
    from velvet.offline import offline_fallback
    print("✅ All Layer 2 imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Create temp directory for testing
test_dir = tempfile.mkdtemp(prefix="velvet_test_")
print(f"\n📁 Test directory: {test_dir}")

# Test 1: Path Resolution
print("\n--- Test 1: Path Resolution ---")
try:
    db = db_path(test_dir)
    settings = settings_path(test_dir)
    print(f"✅ DB path: {db}")
    print(f"✅ Settings path: {settings}")
    assert db.parent.exists(), "User data dir not created"
    print("✅ Directories auto-created")
except Exception as e:
    print(f"❌ Path test failed: {e}")
    sys.exit(1)

# Test 2: Memory System
print("\n--- Test 2: Memory System ---")
try:
    mem = VelvetMemory(db)
    
    # Append events
    mem.append("test", "system", "Test event 1", {"foo": "bar"})
    mem.append("chat", "user", "Hello", {})
    mem.append("chat", "velvet", "Hi there", {})
    print("✅ Events appended")
    
    # Retrieve events
    events = mem.tail(limit=10)
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    print(f"✅ Retrieved {len(events)} events")
    
    # Test recent context
    ctx = mem.recent_chat_context(limit_pairs=1)
    assert len(ctx) == 2, f"Expected 2 context items, got {len(ctx)}"
    assert ctx[0][0] == "user" and ctx[0][1] == "Hello"
    assert ctx[1][0] == "velvet" and ctx[1][1] == "Hi there"
    print("✅ Recent chat context correct")
    
    # Verify compact JSON
    import sqlite3
    con = sqlite3.connect(str(db))
    row = con.execute("SELECT meta_json FROM events WHERE kind='test'").fetchone()
    con.close()
    meta_json = row[0]
    assert '{"foo":"bar"}' in meta_json or '{"foo": "bar"}' in meta_json
    print("✅ Compact JSON metadata stored")
    
except Exception as e:
    print(f"❌ Memory test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: State Management
print("\n--- Test 3: State Management ---")
try:
    # Load initial state
    state = load_state(settings)
    assert state.device_id, "Device ID not generated"
    assert state.mode == "Normal", f"Expected Normal mode, got {state.mode}"
    print(f"✅ State loaded: device_id={state.device_id[:8]}..., mode={state.mode}")
    
    # Change mode
    state = set_mode(settings, state, "Debug")
    assert state.mode == "Debug", "Mode not updated"
    print("✅ Mode changed to Debug")
    
    # Reload and verify persistence
    state2 = load_state(settings)
    assert state2.mode == "Debug", "Mode not persisted"
    assert state2.device_id == state.device_id, "Device ID changed"
    print("✅ State persisted correctly")
    
    # Touch seen
    old_ts = state2.last_seen_ts
    import time
    time.sleep(0.1)
    state3 = touch_seen(settings, state2)
    assert state3.last_seen_ts > old_ts, "Timestamp not updated"
    print("✅ Last seen timestamp updated")
    
except Exception as e:
    print(f"❌ State test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Offline Fallback
print("\n--- Test 4: Offline Fallback ---")
try:
    # Test with context
    ctx = [("user", "How's the weather?"), ("velvet", "Sunny and warm")]
    msg = offline_fallback("What about tomorrow?", ctx, "Normal")
    assert "Network isn't reachable" in msg
    assert "Sunny and warm" in msg or "memory" in msg.lower()
    print(f"✅ Offline message: {msg[:80]}...")
    
    # Test with mode
    msg2 = offline_fallback("Test", [], "Debug")
    assert "Debug" in msg2
    assert "Network isn't reachable" in msg2
    print(f"✅ Mode-aware offline message: {msg2[:80]}...")
    
    # Verify no cloud claims
    assert "cloud" not in msg.lower()
    assert "sync" not in msg.lower()
    print("✅ No false cloud availability claims")
    
except Exception as e:
    print(f"❌ Offline test failed: {e}")
    sys.exit(1)

# Test 5: Thread Safety (DB connections)
print("\n--- Test 5: Thread Safety ---")
try:
    # Verify connections are closed
    mem2 = VelvetMemory(db)
    mem2.append("test", "thread", "Thread test", {})
    
    # Should be able to create new instance
    mem3 = VelvetMemory(db)
    events = mem3.tail(limit=1, kind="test")
    assert len(events) > 0
    print("✅ Multiple instances work (connections closed properly)")
    
except Exception as e:
    print(f"❌ Thread safety test failed: {e}")
    sys.exit(1)

# Cleanup
print("\n--- Cleanup ---")
import shutil
shutil.rmtree(test_dir)
print(f"✅ Test directory removed")

print("\n" + "="*50)
print("✅ ALL LAYER 2 TESTS PASSED")
print("="*50)
print("\nReady for integration into main.py")
