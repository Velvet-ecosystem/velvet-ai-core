"""
Layer 3A: Mode Expression (Light)
Provides subtle tone and presentation shifts based on current mode.
"""

from typing import Dict, Optional

# Mode display labels (how they appear to user)
MODE_LABELS: Dict[str, str] = {
    "Normal": "Velvet",
    "Cautious": "Velvet (Cautious)",
    "Degraded": "Velvet (Limited)",
    "Debug": "Velvet [Debug]",
}

# Tone modifiers for responses (subtle wording shifts)
MODE_TONE_HINTS: Dict[str, str] = {
    "Normal": "",  # Default tone, no modification
    "Cautious": "measured",  # More careful, explicit about uncertainty
    "Degraded": "constrained",  # Acknowledges limitations upfront
    "Debug": "verbose",  # More explicit about internal state
}


def get_mode_label(mode: str) -> str:
    """
    Get display label for a mode.
    
    Args:
        mode: Current mode string (e.g. "Normal", "Cautious")
    
    Returns:
        Display label (e.g. "Velvet", "Velvet (Cautious)")
    """
    return MODE_LABELS.get(mode, f"Velvet ({mode})")


def get_tone_hint(mode: str) -> str:
    """
    Get tone hint for a mode (for potential API prompt modification).
    
    Args:
        mode: Current mode string
    
    Returns:
        Tone descriptor (empty string for Normal mode)
    """
    return MODE_TONE_HINTS.get(mode, "")


def format_ready_message(mode: str) -> str:
    """
    Format the initial "ready" message based on mode.
    
    Args:
        mode: Current mode string
    
    Returns:
        Ready message with appropriate tone
    """
    if mode == "Normal":
        return "Ready."
    elif mode == "Cautious":
        return "Ready. I'll be more explicit about uncertainties."
    elif mode == "Degraded":
        return "Ready, but operating with limited capabilities."
    elif mode == "Debug":
        return "Ready. [Debug mode active - verbose responses enabled]"
    else:
        return f"Ready. (Mode: {mode})"


def apply_mode_context(user_text: str, mode: str) -> str:
    """
    Optionally augment user text with mode context for API.
    Currently a no-op to keep changes minimal.
    
    Args:
        user_text: Original user message
        mode: Current mode string
    
    Returns:
        Text to send to API (currently unchanged)
    """
    # For now, pass through unchanged
    # Future: Could prepend mode instruction like:
    # if mode == "Cautious":
    #     return f"[Respond cautiously] {user_text}"
    return user_text


def format_mode_change_ack(old_mode: str, new_mode: str) -> str:
    """
    Generate acknowledgment message for mode change.
    
    Args:
        old_mode: Previous mode
        new_mode: New mode
    
    Returns:
        Acknowledgment message
    """
    label = get_mode_label(new_mode)
    
    if new_mode == "Normal":
        return "Switched to normal operation."
    elif new_mode == "Cautious":
        return "Switched to cautious mode. I'll be more careful about certainty."
    elif new_mode == "Degraded":
        return "Switched to degraded mode. Some capabilities may be limited."
    elif new_mode == "Debug":
        return "Debug mode enabled. Responses will be more verbose."
    else:
        return f"Mode changed to: {new_mode}"
