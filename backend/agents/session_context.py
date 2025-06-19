"""
Global session context for agent tools
"""
import contextvars
from typing import Optional

# Create a context variable to store the current session ID
_session_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('session_id', default=None)

def set_session_id(session_id: str):
    """Set the current session ID in the context"""
    _session_id_context.set(session_id)

def get_session_id() -> Optional[str]:
    """Get the current session ID from the context"""
    return _session_id_context.get()

def clear_session_id():
    """Clear the current session ID"""
    _session_id_context.set(None)