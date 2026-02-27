"""
Nura - Universal Event-Driven AI Agent Platform

Integrates:
- OpenManus core (Agent, Tool, Flow, Skill)
- Virtual-IP event-driven architecture (EventQueue, Context Management)
- Platform abstraction (MessagingService, TTSService)
- Ark cache integration for token optimization
"""

__version__ = "0.1.0"

# Core schemas and utilities (from OpenManus - core/)
from nura.core.schema import Role, ToolChoice, AgentState, Message, Memory
from nura.core.exceptions import ToolError, TokenLimitExceeded
from nura.core.logger import logger
from nura.core.config import config
from nura.core.cache import CacheManager

# Agents (lazy import to avoid cascading dependencies)
# from nura.agent.base import BaseAgent
# from nura.agent.react import ReActAgent
# from nura.agent.toolcall import ToolCallAgent
# from nura.agent.manus import Manus

# Tools (lazy import to avoid cascading dependencies)
# from nura.tool.base import BaseTool, ToolResult
# from nura.tool.collection import ToolCollection

# Flows (lazy import to avoid cascading dependencies)
# from nura.flow.base import BaseFlow
# from nura.flow.planning import PlanningFlow

# Skills (lazy import to avoid cascading dependencies)
# from nura.skill.manager import SkillManager
# from nura.skill.runner import SkillRunner

# Event system (from Virtual-IP, generalized)
from nura.event import EventQueue, Event, EventType

# Context management (from Virtual-IP, token-based 50% compression)
from nura.context import ContextManager, ContextConfig

# Service abstractions
from nura.services.messaging import MessagingService
from nura.services.tts import TTSService

__all__ = [
    # Core
    "Role", "ToolChoice", "AgentState", "Message", "Memory",
    "logger", "config", "CacheManager",
    # Exceptions
    "ToolError", "TokenLimitExceeded",
    # Events
    "EventQueue", "Event", "EventType",
    # Context (token-based compression)
    "ContextManager", "ContextConfig",
    # Services
    "MessagingService", "TTSService",
]
