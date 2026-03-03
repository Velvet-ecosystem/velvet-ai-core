# Layer 3B: Voice Input (Light) - Behavior Guide

## Overview

Layer 3B adds **optional voice input** to Velvet as a comfort feature for mobile use. Voice is **push-to-talk only**, feeds into the same pipeline as text, and degrades gracefully when unavailable.

**Philosophy**: Comfort and presence, not power.

---

## What Was Added

### Voice Input Module (`velvet/voice_input.py`)

**Platform Support**:
- ✅ Android: Uses Android SpeechRecognizer via `plyer.stt`
- ❌ Desktop/iOS: Gracefully unavailable (no error, just hidden)

**Interface**:
```python
VoiceInput():
  - is_available: bool           # Platform supports voice?
  - is_listening: bool            # Currently recording?
  - start_listening(on_result, on_error) → bool
  - stop_listening()
  - get_last_result() → str
  - get_unavailability_reason() → str
```

### UI Changes (Minimal)

**Mic Button** (Android only):
- Location: Left of text input
- Size: 15% width (text input shrinks to 60%)
- Visual: 🎤 emoji, dark gray background
- Behavior: Press to start, release to stop

**No mic button on desktop** - feature auto-hides when unavailable.

### Permission Added

**buildozer.spec**:
```
android.permissions = INTERNET,ACCESS_NETWORK_STATE,RECORD_AUDIO
```

**RECORD_AUDIO**: Required for microphone access on Android.

---

## How Voice Input Works

### User Flow

```
1. User PRESSES mic button (🎤)
   ↓
2. Button changes: 🎤 ... (purple background)
   ↓
3. Android STT starts listening
   ↓
4. User speaks: "What's the weather like?"
   ↓
5. User RELEASES mic button
   ↓
6. Android STT processes speech
   ↓
7. Transcribed text appears in text input
   ↓
8. User can EDIT text if needed
   ↓
9. User presses Send (same as typed message)
```

**Key Point**: Voice **feeds into text input**, not directly to chat. User stays in control.

### Push-to-Talk Only

❌ **NOT** always-listening  
❌ **NOT** wake-word activated  
❌ **NOT** background recording  
✅ **YES** explicit press-and-hold  
✅ **YES** user-initiated  
✅ **YES** visual feedback  

### Integration with Existing Pipeline

Voice transcription → Text input → (user edits) → Send → Same chat flow as typed messages

**No difference** between voice and text after transcription.

---

## Platform Behavior

### Android (Voice Available)

**First Use**:
1. User presses mic button
2. Android shows permission dialog: "Allow Velvet to record audio?"
3. User accepts → Voice works
4. User denies → Button hidden, fallback message shown

**Normal Use**:
- Mic button visible
- Press = start listening
- Release = stop, transcribe
- Result appears in text input

**Offline**:
- Android STT works offline (on-device recognition)
- No network required for transcription
- If device doesn't support offline STT:
  - Error message: "I can't do voice input right now, but you can type."

### Desktop (Voice Unavailable)

- Mic button **not shown** (auto-hidden)
- Text input uses full width (75%)
- No error messages (seamless degradation)
- Typing works normally

### iOS (Not Implemented)

- Same as desktop: graceful unavailability
- Could be added in future with iOS STT APIs

---

## Error Handling

### Voice Unavailable (Platform)

**Message**: "Voice input is only available on Android devices."  
**UI**: Mic button not shown  
**Action**: User continues with text input  

### Voice Unavailable (Permission Denied)

**Message**: "I can't do voice input right now, but you can type."  
**UI**: Mic button hidden after first denial  
**Action**: User continues with text input  

### STT Failure (Network/Processing)

**Message**: "Voice input failed: [reason]"  
**UI**: Button resets to inactive state  
**Action**: User can try again or type  

### No Result (User Released Too Soon)

**Behavior**: Button resets, no message  
**UI**: Silent failure (not an error, just incomplete)  
**Action**: User can press again  

---

## Mode Interaction (Layer 3A)

Voice input **respects** current mode but **does not change** based on mode.

| Mode | Voice Behavior |
|------|---------------|
| Normal | Standard transcription |
| Cautious | Transcription unchanged (mode affects response only) |
| Degraded | Voice still works if platform supports it |
| Debug | Transcription unchanged (no special verbose mode) |

**Key**: Mode affects **how Velvet responds**, not **how voice works**.

---

## Memory Integration (Layer 2)

Voice-transcribed messages are logged the same as typed messages:

```python
# User speaks → transcribed to "What's the weather?"
# User presses Send
memory.append("chat", "user", "What's the weather?", {})
```

**No distinction** between voice and text in memory log. It's all just chat.

---

## Offline Behavior

### Android On-Device STT

Most modern Android devices support **offline speech recognition**:
- No network required
- Fast transcription
- Works in airplane mode
- Works in Degraded mode

### Android Cloud STT (Fallback)

Some devices only support cloud-based STT:
- Requires network connection
- Fails gracefully if offline
- Error message: "I can't do voice input right now, but you can type."

**Velvet is honest**: If voice needs network and network is down, Velvet says so.

---

## Privacy & Honesty

### What Velvet Says (If Cloud STT)

If Android STT uses cloud processing, Velvet should be honest:

```
(Future enhancement - not yet implemented)
On first voice use:
"Voice input uses Android's speech recognition, which may send 
 audio to Google for processing. You can type instead if you prefer."
```

**Current implementation**: Relies on Android system STT without additional disclosure (assuming user is aware Android STT may use cloud).

### What Velvet Does NOT Do

❌ Store audio recordings  
❌ Send audio to Anthropic servers  
❌ Analyze voice patterns  
❌ Use voice for authentication  
❌ Record in background  
❌ Train models on user speech  

Voice is **transcription-only**, then discarded.

---

## Testing Voice Input

### Manual Test Checklist (Android Device)

**Setup**:
1. Deploy app to Android device
2. Grant RECORD_AUDIO permission when prompted

**Test 1: Basic Voice Input**:
- [ ] Mic button visible (🎤 emoji)
- [ ] Press mic button → button turns purple, shows "🎤 ..."
- [ ] Speak: "Hello Velvet"
- [ ] Release mic button
- [ ] Text appears in input field: "Hello Velvet"
- [ ] Edit if needed
- [ ] Press Send → message sent as normal

**Test 2: Voice Flow**:
- [ ] Press mic
- [ ] Speak: "What's the weather like?"
- [ ] Release
- [ ] Transcribed text appears
- [ ] Send → Velvet responds (or offline fallback)
- [ ] Memory logs "What's the weather like?" as chat/user

**Test 3: Error Cases**:
- [ ] Airplane mode ON
- [ ] Press mic → STT may fail
- [ ] Error message shown: "I can't do voice input right now, but you can type."
- [ ] Button resets
- [ ] Can still type normally

**Test 4: Permission Denied**:
- [ ] Uninstall/reinstall app
- [ ] Press mic → permission prompt
- [ ] Deny permission
- [ ] Mic button hides
- [ ] App continues normally with text input

**Test 5: Quick Release**:
- [ ] Press mic briefly (< 0.5 sec)
- [ ] Release before speaking
- [ ] Button resets, no error
- [ ] Can press again

**Test 6: Mode Integration**:
- [ ] `/mode Cautious`
- [ ] Press mic, speak "Test"
- [ ] Transcription works normally
- [ ] Send → Response reflects Cautious mode (not transcription)

---

## Design Decisions

### Why Push-to-Talk?

**Comfort**: User controls exactly when they're being recorded  
**Privacy**: No accidental recording, no background listening  
**Clarity**: Explicit intent, no ambiguity about recording state  
**Battery**: No continuous audio processing  

### Why Feed to Text Input (Not Direct Send)?

**Control**: User can review/edit before sending  
**Correction**: STT isn't perfect, user can fix errors  
**Consistency**: Same UX as typing (review → send)  
**Safety**: No accidental sends from misheard words  

### Why Android-Only (For Now)?

**Simplicity**: Single platform keeps implementation minimal  
**Coverage**: Android is primary mobile target  
**Plyer Support**: Well-tested Android STT integration  
**Reversibility**: Easy to add iOS later without breaking changes  

---

## Future Enhancements (Not Implemented)

### Potential Additions

1. **iOS Support**: Add iOS STT via plyer
2. **Language Selection**: Support non-English input
3. **STT Confidence**: Show low-confidence words highlighted
4. **Quick Send**: Optional "auto-send" after transcription
5. **Voice Activity Detection**: Auto-stop when user stops speaking
6. **Privacy Notice**: Explicit disclosure if cloud STT is used

### NOT Planned

❌ Wake word detection  
❌ Voice biometrics  
❌ Speaker identification  
❌ Emotion detection  
❌ Background recording  
❌ Voice commands (hands-free control)  

Voice is **input only**, not a control interface.

---

## Reversibility

### Full Removal (3 Steps)

1. **Delete module**: `rm velvet/voice_input.py`
2. **Remove import**: Delete voice_input imports from `main.py`
3. **Remove UI**: Delete mic button code from `build()`
4. **Revert permission**: Remove `RECORD_AUDIO` from buildozer.spec

**No data migration needed**. Voice input leaves no persistent state.

### Partial Removal (Hide Feature)

Change in `main.py`:
```python
# Force voice unavailable
self.mic_btn = None  # Don't create mic button
```

Feature hidden, code remains for potential future use.

---

## Performance Impact

### App Size

**Module**: ~4 KB (voice_input.py)  
**Dependencies**: None (uses plyer, already included)  
**Total increase**: ~4 KB  

### Runtime Overhead

**When not used**: Zero (button check is trivial)  
**When listening**: Android STT handles processing  
**Memory**: Negligible (no buffering in Velvet)  
**Battery**: Only during active recording  

---

## Comparison: Before vs After

### Before Layer 3B

```
┌─────────────────────────────┐
│  Velvet (Mode)              │
└─────────────────────────────┘

[Text Input                 ] [Send]

User types message → Send → Chat
```

### After Layer 3B (Android)

```
┌─────────────────────────────┐
│  Velvet (Mode)              │
└─────────────────────────────┘

[🎤] [Text Input          ] [Send]
 ↑     ↑                      ↑
Voice  Typing               Same
option (primary)          pipeline

User speaks OR types → (edit) → Send → Chat
```

**Difference**: Voice is an **optional input method**, not a separate interface.

---

## Summary

**What voice adds**:
- Optional mic button (Android only)
- Press-to-talk recording
- Transcription to text input
- Same chat pipeline

**What voice does NOT add**:
- Always-listening
- Wake words
- Background recording
- Separate voice commands
- Voice responses
- New logic or automation

**Philosophy**: Voice is a **comfortable way to input text** while mobile, not a different assistant mode.

---

*End of Layer 3B Behavior Guide*
