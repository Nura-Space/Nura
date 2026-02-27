from typing import Optional

from nura.llm.adapters.ark import ArkMessageAdapter
from nura.llm.adapters.base import BaseMessageAdapter
from nura.llm.adapters.openai import OpenAIMessageAdapter


def get_message_adapter(provider: str) -> BaseMessageAdapter:
    """Factory function to get the appropriate message adapter.

    Args:
        provider: Provider identifier ("openai", "ark", "azure", etc.)

    Returns:
        BaseMessageAdapter instance for the provider

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()

    if provider in ("openai", "azure"):
        return OpenAIMessageAdapter()
    elif provider == "ark":
        return ArkMessageAdapter()
    else:
        # Default to OpenAI adapter for unknown providers
        return OpenAIMessageAdapter()


def is_ark_provider(base_url: Optional[str]) -> bool:
    """Check if the base_url indicates an Ark provider.

    Args:
        base_url: The API base URL

    Returns:
        True if the URL indicates Ark provider
    """
    if not base_url:
        return False
    return "volces.com" in base_url


__all__ = [
    "BaseMessageAdapter",
    "OpenAIMessageAdapter",
    "ArkMessageAdapter",
    "get_message_adapter",
    "is_ark_provider",
]
