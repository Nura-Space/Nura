from typing import Any, Dict, List, Optional, Union

from openai.types.chat import ChatCompletionMessage

from nura.llm.adapters.base import BaseMessageAdapter


class OpenAIMessageAdapter(BaseMessageAdapter):
    """Message adapter for OpenAI provider.

    This is a pass-through adapter since OpenAI's format is the standard.
    """

    def format_for_provider(
        self,
        messages: List[Union[Dict[str, Any], Any]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Return messages as-is (OpenAI is the standard format).

        Args:
            messages: List of messages in standard OpenAI format
            tools: Optional list of tools (returned as-is)
            tool_choice: Optional tool choice (returned as-is)

        Returns:
            List of messages in OpenAI format (unchanged)
        """
        # Convert any Message objects to dicts
        formatted = []
        for message in messages:
            if hasattr(message, "to_dict"):
                formatted.append(message.to_dict())
            elif hasattr(message, "dict"):
                formatted.append(message.dict())
            else:
                formatted.append(message)
        return formatted

    def parse_response(self, response: Any) -> ChatCompletionMessage:
        """Return the message from response as-is.

        Args:
            response: ChatCompletion response from OpenAI

        Returns:
            ChatCompletionMessage from the response
        """
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message
        raise ValueError("Invalid OpenAI response format")

    def format_tools(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Return tools as-is (OpenAI format is standard).

        Args:
            tools: List of tools in OpenAI format

        Returns:
            Same tools list
        """
        return tools

    def format_tool_choice(
        self, tool_choice: Optional[Union[str, Dict]]
    ) -> Optional[Union[str, Dict]]:
        """Return tool choice as-is.

        Args:
            tool_choice: Tool choice in standard format

        Returns:
            Same tool choice
        """
        return tool_choice
