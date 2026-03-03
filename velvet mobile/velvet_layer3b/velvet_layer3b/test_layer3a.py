#!/usr/bin/env python3
"""
Layer 3A Verification Test
Tests mode expression functionality
"""

import sys

# Test imports
try:
    from velvet import mode_expression
    print("✅ mode_expression import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("LAYER 3A: MODE EXPRESSION TESTS")
print("="*50)

# Test 1: Mode Labels
print("\n--- Test 1: Mode Labels ---")
modes = ["Normal", "Cautious", "Degraded", "Debug", "CustomMode"]
for mode in modes:
    label = mode_expression.get_mode_label(mode)
    print(f"  {mode:12} → {label}")

assert mode_expression.get_mode_label("Normal") == "Velvet"
assert mode_expression.get_mode_label("Cautious") == "Velvet (Cautious)"
assert mode_expression.get_mode_label("Degraded") == "Velvet (Limited)"
assert mode_expression.get_mode_label("Debug") == "Velvet [Debug]"
assert "CustomMode" in mode_expression.get_mode_label("CustomMode")
print("✅ Mode labels correct")

# Test 2: Tone Hints
print("\n--- Test 2: Tone Hints ---")
for mode in ["Normal", "Cautious", "Degraded", "Debug"]:
    hint = mode_expression.get_tone_hint(mode)
    if hint:
        print(f"  {mode:12} → tone: {hint}")
    else:
        print(f"  {mode:12} → (default tone)")

assert mode_expression.get_tone_hint("Normal") == ""
assert mode_expression.get_tone_hint("Cautious") == "measured"
assert mode_expression.get_tone_hint("Degraded") == "constrained"
assert mode_expression.get_tone_hint("Debug") == "verbose"
print("✅ Tone hints correct")

# Test 3: Ready Messages
print("\n--- Test 3: Ready Messages ---")
for mode in ["Normal", "Cautious", "Degraded", "Debug", "Unknown"]:
    msg = mode_expression.format_ready_message(mode)
    print(f"  {mode:12} → \"{msg}\"")

# Verify they're different and contextual
normal_msg = mode_expression.format_ready_message("Normal")
cautious_msg = mode_expression.format_ready_message("Cautious")
degraded_msg = mode_expression.format_ready_message("Degraded")

assert normal_msg == "Ready."
assert "uncertain" in cautious_msg.lower() or "explicit" in cautious_msg.lower()
assert "limit" in degraded_msg.lower() or "capabilit" in degraded_msg.lower()
print("✅ Ready messages appropriate for each mode")

# Test 4: Mode Context (No-op check)
print("\n--- Test 4: Mode Context Application ---")
test_text = "Hello, how are you?"
for mode in ["Normal", "Cautious", "Degraded"]:
    result = mode_expression.apply_mode_context(test_text, mode)
    # Currently should be pass-through
    assert result == test_text, f"Expected pass-through for {mode}"
    print(f"  {mode:12} → (pass-through, no modification)")
print("✅ Mode context is pass-through (minimal changes)")

# Test 5: Mode Change Acknowledgments
print("\n--- Test 5: Mode Change Acknowledgments ---")
transitions = [
    ("Normal", "Cautious"),
    ("Cautious", "Degraded"),
    ("Degraded", "Normal"),
    ("Normal", "Debug"),
]

for old, new in transitions:
    ack = mode_expression.format_mode_change_ack(old, new)
    print(f"  {old:10} → {new:10}: \"{ack}\"")

# Verify they're informative
cautious_ack = mode_expression.format_mode_change_ack("Normal", "Cautious")
assert "cautious" in cautious_ack.lower()
print("✅ Mode change acknowledgments informative")

# Test 6: String-based (No Enums)
print("\n--- Test 6: String-Based Design ---")
# All functions should accept any string
custom_label = mode_expression.get_mode_label("MyCustomMode")
assert isinstance(custom_label, str)
print(f"  Custom mode 'MyCustomMode' → \"{custom_label}\"")
print("✅ Accepts arbitrary mode strings (no enum requirement)")

# Test 7: Expression Subtlety
print("\n--- Test 7: Expression Subtlety Check ---")
messages = {
    "Normal": mode_expression.format_ready_message("Normal"),
    "Cautious": mode_expression.format_ready_message("Cautious"),
    "Degraded": mode_expression.format_ready_message("Degraded"),
}

for mode, msg in messages.items():
    # Check message isn't too verbose (restraint over cleverness)
    assert len(msg) < 100, f"{mode} message too long: {len(msg)} chars"
    # Check it doesn't use overly dramatic language
    drama_words = ["critical", "emergency", "severe", "danger", "warning"]
    assert not any(word in msg.lower() for word in drama_words), f"{mode} message too dramatic"

print("  All messages under 100 chars, no dramatic language")
print("✅ Expression is subtle and restrained")

print("\n" + "="*50)
print("✅ ALL LAYER 3A TESTS PASSED")
print("="*50)
print("\nMode expression summary:")
print("  - Labels: Subtle visual indicator in title")
print("  - Tone: Reserved for future API integration")
print("  - Messages: Context-appropriate, non-invasive")
print("  - Changes: Minimal and reversible")
