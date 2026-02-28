from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from openai.types.chat import ChatCompletionMessage


class BaseMessageAdapter(ABC):
    """Abstract base class for LLM provider message adapters.

    Each adapter converts messages between the standard OpenAI format
    and the specific format required by different LLM providers.
    """

    @abstractmethod
    def format_for_provider(
        self,
        messages: List[Union[Dict[str, Any], Any]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert standard messages to provider-specific format.

        Args:
            messages: List of messages in standard format
            tools: Optional list of tools to include
            tool_choice: Optional tool choice configuration

        Returns:
            List of messages in provider-specific format
        """
        pass

    @abstractmethod
    def parse_response(self, response: Any) -> ChatCompletionMessage:
        """Parse provider response to standard ChatCompletionMessage format.

        Args:
            response: Raw response from the LLM provider

        Returns:
            ChatCompletionMessage in standard OpenAI format
        """
        pass

    def format_tools(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Convert tools to provider-specific format.

        Args:
            tools: List of tools in standard OpenAI format

        Returns:
            List of tools in provider-specific format, or None if no tools
        """
        if tools is None:
            return None
        return tools

    def format_tool_choice(
        self, tool_choice: Optional[Union[str, Dict]]
    ) -> Optional[Union[str, Dict]]:
        """Format tool choice to provider-specific format.

        Args:
            tool_choice: Tool choice in standard format

        Returns:
            Tool choice in provider-specific format
        """
        return tool_choice
