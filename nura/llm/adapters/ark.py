from typing import Any, Dict, List, Optional, Union

from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from nura.llm.adapters.base import BaseMessageAdapter


class ArkMessageAdapter(BaseMessageAdapter):
    """Message adapter for Volcengine Ark (volces.com) provider.

    Converts between OpenAI message format and Ark's proprietary format:
    - OpenAI tool_calls → Ark function_call
    - OpenAI tool messages → Ark function_call_output
    """

    def format_for_provider(
        self,
        messages: List[Union[Dict[str, Any], Any]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
    ) -> List[Dict[str, Any]]:
        """Convert standard OpenAI messages to Ark format.

        Args:
            messages: List of messages in OpenAI format
            tools: Optional list of tools in OpenAI format
            tool_choice: Optional tool choice configuration

        Returns:
            List of messages in Ark format
        """
        ark_messages = []

        for message in messages:
            # Convert to dict if needed
            if hasattr(message, "to_dict"):
                message = message.to_dict()
            elif hasattr(message, "dict"):
                message = message.dict()

            if message.get("role") == "assistant" and "tool_calls" in message:
                # Convert OpenAI tool_calls to Ark function_call
                for tool_call in message.get("tool_calls", []):
                    ark_messages.append(
                        {
                            "type": "function_call",
                            "call_id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "arguments": tool_call["function"]["arguments"],
                        }
                    )
            elif message.get("role") == "tool":
                # Convert OpenAI tool message to Ark function_call_output
                ark_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": message["tool_call_id"],
                        "output": message["content"],
                    }
                )
            elif message.get("role") == "user" and message.get("base64_image"):
                # Handle user message with base64 image for Ark format
                content = message.get("content", "")
                ark_messages.append(
                    {
                        "role": "user",
                        "type": "message",
                        "content": [
                            {"type": "input_text", "text": content} if content else {},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{message['base64_image']}",
                            },
                        ],
                    }
                )
            else:
                # Pass through regular messages
                ark_messages.append(message)

        return ark_messages

    def parse_response(self, response: Any) -> ChatCompletionMessage:
        """Parse Ark response to OpenAI ChatCompletionMessage format.

        Args:
            response: Response from Ark API (using responses endpoint)

        Returns:
            ChatCompletionMessage in standard OpenAI format
        """
        content = ""
        reasoning_content = ""
        tool_calls = []

        # Parse response.output which contains message, reasoning, and function_call items
        for item in response.output:
            if item.type == "message":
                if hasattr(item, "content"):
                    for content_item in item.content:
                        if content_item.type == "output_text":
                            content += content_item.text
            elif item.type == "reasoning":
                if hasattr(item, "summary"):
                    for summary in item.summary:
                        if hasattr(summary, "text"):
                            reasoning_content += summary.text
            elif item.type == "function_call":
                tool_calls.append(
                    ChatCompletionMessageToolCall(
                        id=item.call_id,
                        function=Function(name=item.name, arguments=item.arguments),
                        type="function",
                    )
                )

        message = ChatCompletionMessage(
            role="assistant",
            content=content,
            tool_calls=tool_calls if tool_calls else None,
        )

        # Attach reasoning_content if present
        if reasoning_content:
            message.reasoning_content = reasoning_content

        return message

    def format_tools(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Convert OpenAI tools to Ark format.

        Args:
            tools: List of tools in OpenAI format

        Returns:
            List of tools in Ark format
        """
        if tools is None:
            return None

        return [
            {
                "type": "function",
                "name": tool.get("function", {}).get("name", ""),
                "description": tool.get("function", {}).get("description", ""),
                "parameters": tool.get("function", {}).get("parameters", {}),
            }
            for tool in tools
        ]

    def format_tool_choice(
        self, tool_choice: Optional[Union[str, Dict]]
    ) -> Optional[Union[str, Dict]]:
        """Format tool choice to Ark format.

        Args:
            tool_choice: Tool choice in standard format

        Returns:
            Tool choice in Ark format
        """
        return tool_choice
