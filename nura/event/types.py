"""Event types for Nura event system."""
from enum import Enum
from typing import Any
from dataclasses import dataclass, field
import time

class EventType(str, Enum):
    """Event types for routing"""
    MAIN = "main"              # User messages (high priority)
    BACKGROUND = "background"  # Async tasks (lower priority)

@dataclass
class Event:
    """Event wrapper"""
    id: str
    type: EventType
    data: Any
    conversation_id: str
    timestamp: float = field(default_factory=time.time)
