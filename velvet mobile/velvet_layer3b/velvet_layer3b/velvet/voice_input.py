"""
Layer 3B: Voice Input (Light)
Minimal voice-to-text input using Android platform APIs.
Push-to-talk only, no background recording.
"""

from typing import Optional, Callable
from kivy.utils import platform


class VoiceInput:
    """
    Simple voice input handler using platform-native speech recognition.
    Android: Uses Android SpeechRecognizer via plyer
    Desktop: Gracefully degrades (not supported)
    """
    
    def __init__(self):
        self.is_available = False
        self.is_listening = False
        self._stt = None
        self._on_result_callback = None
        self._on_error_callback = None
        
        # Initialize platform-specific STT
        if platform == 'android':
            try:
                from plyer import stt
                self._stt = stt
                self.is_available = True
            except Exception:
                self.is_available = False
        else:
            # Desktop/iOS - not supported in this light implementation
            self.is_available = False
    
    def start_listening(self, 
                       on_result: Callable[[str], None],
                       on_error: Optional[Callable[[str], None]] = None) -> bool:
        """
        Start listening for voice input (push-to-talk).
        
        Args:
            on_result: Callback for transcribed text (string)
            on_error: Optional callback for errors (string message)
        
        Returns:
            True if listening started, False if unavailable
        """
        if not self.is_available or self.is_listening:
            return False
        
        self._on_result_callback = on_result
        self._on_error_callback = on_error
        
        try:
            # Start Android STT
            self._stt.start()
            self.is_listening = True
            return True
        except Exception as e:
            if self._on_error_callback:
                self._on_error_callback(f"Voice input failed: {str(e)}")
            return False
    
    def stop_listening(self):
        """Stop listening (if active)."""
        if not self.is_listening:
            return
        
        try:
            if self._stt:
                self._stt.stop()
        except Exception:
            pass
        
        self.is_listening = False
    
    def get_last_result(self) -> Optional[str]:
        """
        Get the last transcription result from Android STT.
        
        Returns:
            Transcribed text or None
        """
        if not self._stt:
            return None
        
        try:
            results = self._stt.results
            if results and len(results) > 0:
                # Return the first (most confident) result
                return results[0]
        except Exception:
            return None
        
        return None
    
    def check_result(self) -> Optional[str]:
        """
        Check for completed transcription result.
        Call this periodically or in response to STT completion.
        
        Returns:
            Transcribed text if available, None otherwise
        """
        if not self.is_listening:
            return None
        
        result = self.get_last_result()
        if result:
            self.stop_listening()
            if self._on_result_callback:
                self._on_result_callback(result)
            return result
        
        return None
    
    def get_unavailability_reason(self) -> str:
        """
        Get human-readable reason why voice input is unavailable.
        
        Returns:
            Error message for user display
        """
        if platform != 'android':
            return "Voice input is only available on Android devices."
        
        if not self.is_available:
            return "Voice input isn't available on this device."
        
        return "Voice input is available."


# Singleton instance (created on demand)
_voice_input_instance: Optional[VoiceInput] = None


def get_voice_input() -> VoiceInput:
    """Get or create the global voice input instance."""
    global _voice_input_instance
    if _voice_input_instance is None:
        _voice_input_instance = VoiceInput()
    return _voice_input_instance


def is_voice_available() -> bool:
    """Check if voice input is available on this platform."""
    return get_voice_input().is_available
