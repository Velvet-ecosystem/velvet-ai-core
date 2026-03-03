# Layer 3A: Mode Expression - What Changes When Mode Changes

## Overview

Layer 3A adds **subtle, non-invasive** mode expression to Velvet. Mode affects **tone and presentation only** — no logic, automation, or capabilities are gated.

---

## Visual Changes (Minimal)

### Title Bar Indicator

**Normal Mode**:
```
┌────────────────────┐
│      VELVET        │  ← Clean, simple
└────────────────────┘
```

**Cautious Mode**:
```
┌────────────────────┐
│ Velvet (Cautious)  │  ← Parenthetical indicator
└────────────────────┘
```

**Degraded Mode**:
```
┌────────────────────┐
│  Velvet (Limited)  │  ← Shows limitation status
└────────────────────┘
```

**Debug Mode**:
```
┌────────────────────┐
│  Velvet [Debug]    │  ← Bracket notation for dev mode
└────────────────────┘
```

**That's it.** No color changes, no animations, no layout restructuring.

---

## Tone Changes (Wording Only)

### Ready Messages

| Mode | Welcome Message |
|------|----------------|
| Normal | "Ready." |
| Cautious | "Ready. I'll be more explicit about uncertainties." |
| Degraded | "Ready, but operating with limited capabilities." |
| Debug | "Ready. [Debug mode active - verbose responses enabled]" |

### Mode Switch Acknowledgments

When you change modes (e.g., `/mode Cautious`):

| Transition | Acknowledgment |
|-----------|---------------|
| → Normal | "Switched to normal operation." |
| → Cautious | "Switched to cautious mode. I'll be more careful about certainty." |
| → Degraded | "Switched to degraded mode. Some capabilities may be limited." |
| → Debug | "Debug mode enabled. Responses will be more verbose." |

---

## What Modes Mean (Intent)

### Normal
- **Default**: Standard conversational tone
- **Visual**: "Velvet"
- **Tone**: Natural, direct responses
- **Use**: Everyday interaction

### Cautious
- **Intent**: More explicit about uncertainty and confidence levels
- **Visual**: "Velvet (Cautious)"
- **Tone**: "measured" — acknowledges limitations more clearly
- **Use**: When precision and honesty about uncertainty matter
- **Future API**: Could prepend "[Respond cautiously, be explicit about confidence]"

### Degraded
- **Intent**: Operating with reduced capabilities or connectivity issues
- **Visual**: "Velvet (Limited)"
- **Tone**: "constrained" — upfront about what's available
- **Use**: Offline mode, reduced functionality scenarios
- **Future API**: Could indicate limited model access

### Debug
- **Intent**: Development and troubleshooting
- **Visual**: "Velvet [Debug]"
- **Tone**: "verbose" — more internal state information
- **Use**: Testing, development, understanding internal behavior
- **Future API**: Could enable detailed step-by-step reasoning

---

## What Does NOT Change

❌ **No Logic Changes**: Mode doesn't enable/disable features  
❌ **No Automation**: Mode doesn't trigger actions  
❌ **No Permissions**: Mode doesn't affect what Velvet can access  
❌ **No UI Redesign**: Layout remains identical  
❌ **No Animations**: No transitions or visual effects  
❌ **No Capability Gating**: All functions available in all modes  

Mode is **expressive**, not **prescriptive**.

---

## Testing Modes (Development)

### Command Line (In App)

Type in the chat:
```
/mode Cautious    → Switch to Cautious
/mode Degraded    → Switch to Degraded
/mode Debug       → Switch to Debug
/mode Normal      → Back to Normal
```

The app will:
1. Update the title bar label
2. Show acknowledgment message
3. Persist the mode to state file

### Programmatic (For API Integration)

```python
from velvet.state import set_mode

# Change mode
app.state = set_mode(app.settings_file, app.state, "Cautious")

# Get current mode for API calls
current_mode = app.state.mode

# Get tone hint for prompting
from velvet.mode_expression import get_tone_hint
tone = get_tone_hint(current_mode)
# Use 'tone' in API prompt construction
```

---

## Future API Integration Points

### Tone Injection (Reserved, Not Yet Implemented)

```python
# In api.py chat() function:
from velvet.mode_expression import get_tone_hint, apply_mode_context

def chat(user_text, recent_context, mode):
    tone = get_tone_hint(mode)
    
    # Option A: Prepend to user message
    if mode == "Cautious":
        prompt = f"[Be measured and explicit about uncertainty] {user_text}"
    
    # Option B: System prompt modification
    system_prompt = f"You are Velvet. Respond in a {tone} tone." if tone else "You are Velvet."
    
    # Option C: Post-process response
    response = call_api(user_text)
    if mode == "Debug":
        response = f"[Debug] {response}\n[Mode: {mode}, Context items: {len(recent_context)}]"
    
    return response
```

Currently `apply_mode_context()` is a **pass-through** — this is intentional for minimal integration.

---

## Reversibility

All changes are **easily reversible**:

1. **Remove title update**: Delete `_update_mode_display()` call
2. **Remove mode command**: Delete mode change detection in `_process_message()`
3. **Remove ready message variation**: Use static "Ready." string
4. **Remove module**: Delete `mode_expression.py`, remove from imports

No data migrations needed, no compatibility issues.

---

## Design Philosophy

**Restraint over Cleverness**:
- Short messages (< 100 chars)
- No dramatic language
- No color coding or badges
- No persistent notifications
- No unsolicited mode suggestions

**Honest Communication**:
- Mode label visible but unobtrusive
- Clear acknowledgment when mode changes
- No hidden behavior differences
- User always in control

**Future-Proof**:
- Tone hints ready for API integration
- Mode context hook available but unused
- String-based design allows custom modes
- No hardcoded assumptions about behavior

---

## Example User Experience

### Scenario: Network Issues

**Before Layer 3A**:
```
User: "What's the weather like?"
Velvet: "Network isn't reachable right now. You can rephrase, or tell me 
         what you want to stage locally."
```

**After Layer 3A** (if mode auto-switches to Degraded):
```
Title: "Velvet (Limited)"  ← Subtle visual cue
User: "What's the weather like?"
Velvet: "Network isn't reachable right now. You can rephrase, or tell me 
         what you want to stage locally."
```

Same response, but user has **visual context** about operating state.

### Scenario: User Wants Cautious Responses

```
User: "/mode Cautious"
Title: "Velvet (Cautious)"  ← Updates immediately
System: "Switched to cautious mode. I'll be more careful about certainty."

User: "Is this stock a good investment?"
Velvet: [In future with API integration, response would explicitly 
         acknowledge uncertainty, cite confidence levels, etc.]
```

---

## Summary

**What changes**:
- Title bar label (1 line of text)
- Welcome message (1 sentence)
- Mode switch acknowledgment (1 sentence)

**What's reserved for future**:
- Tone injection in API calls
- Response post-processing
- Context prepending

**What never changes**:
- App logic
- UI layout
- Capabilities
- Permissions
- Performance

Mode is a **hint**, not a **command**.
