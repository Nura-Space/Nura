"""Base cache abstract class."""
# pylint: disable=duplicate-code
# The factory method and its calls have similar structure by design.

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Union

from nura.core.schema import Message


@dataclass
class LLMRequestParams:
    """Parameters for LLM requests, used to reduce duplicate parameter lists."""

    client: Any
    model: str
    messages: List[Union[dict, Message]]
    request_builder: Any
    max_tokens: int
    temperature: float
    system_msgs: Optional[List[Union[dict, Message]]] = None
    tools: Optional[List[dict]] = None
    tool_choice: Optional[Union[str, dict]] = None
    session_id: Optional[str] = None
    supports_images: bool = False

    @classmethod
    def create(
        cls,
        client: Any,
        model: str,
        messages: List[Union[dict, Message]],
        request_builder: Any,
        max_tokens: int,
        temperature: float,
        system_msgs: Optional[List[Union[dict, Message]]] = None,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        session_id: Optional[str] = None,
        supports_images: bool = False,
    ) -> "LLMRequestParams":
        """Factory method to create LLMRequestParams with all parameters."""
        return cls(
            client=client,
            model=model,
            messages=messages,
            request_builder=request_builder,
            max_tokens=max_tokens,
            temperature=temperature,
            system_msgs=system_msgs,
            tools=tools,
            tool_choice=tool_choice,
            session_id=session_id,
            supports_images=supports_images,
        )


class BaseCache(ABC):
    """Abstract base class for LLM caching."""

    @abstractmethod
    async def ask(
        self,
        params: LLMRequestParams,
    ) -> Any:
        """Execute LLM request with caching.

        Args:
            params: LLM request parameters

        Returns:
            Parsed response (message or dict with metadata)
        """
        pass

    @abstractmethod
    def supports_cache(self, base_url: Optional[str]) -> bool:
        """Check if this cache supports the given base_url.

        Args:
            base_url: The API base URL

        Returns:
            True if this cache supports the URL
        """
        pass
