"""
Velvet API client module.
Placeholder for remote AI service calls.
"""
from typing import Dict, List, Tuple, Optional

def chat(user_text: str, 
         recent_context: Optional[List[Tuple[str, str]]] = None,
         mode: str = "Normal") -> str:
    """
    Send chat message to Velvet AI service.
    
    Args:
        user_text: User's message
        recent_context: Recent conversation history [(speaker, text), ...]
        mode: Current conversation mode
    
    Returns:
        AI response text
        
    Raises:
        Exception: On network or API errors
    """
    # TODO: Implement actual API call
    # For now, return placeholder
    raise NotImplementedError("API integration pending")
