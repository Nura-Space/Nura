"""LLM module for interacting with various LLM providers.

This module provides:
- TokenCounter: Token counting for messages
- LLM: Main client for LLM interactions
- format_messages: Message formatting utility
- REASONING_MODELS, MULTIMODAL_MODELS: Model constant lists
- adapters: Message adapter system for different providers
"""
# Re-export for backward compatibility
from nura.llm.client import LLM
from nura.llm.constants import MULTIMODAL_MODELS, REASONING_MODELS
from nura.llm.message import format_messages
from nura.llm.token_counter import TokenCounter

# Re-export adapters
from nura.llm.adapters import (
    ArkMessageAdapter,
    BaseMessageAdapter,
    OpenAIMessageAdapter,
    get_message_adapter,
    is_ark_provider,
)

# Re-export BedrockClient (optional)
try:
    from nura.llm.bedrock import BedrockClient
except ImportError:
    BedrockClient = None  # Bedrock is optional

__all__ = [
    # Main classes
    "LLM",
    "TokenCounter",
    # Constants
    "REASONING_MODELS",
    "MULTIMODAL_MODELS",
    # Functions
    "format_messages",
    # Adapters
    "BaseMessageAdapter",
    "OpenAIMessageAdapter",
    "ArkMessageAdapter",
    "get_message_adapter",
    "is_ark_provider",
    # Optional
    "BedrockClient",
]
