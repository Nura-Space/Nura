"""Message formatting utilities for LLM providers."""
from typing import List, Union

from nura.core.schema import ROLE_VALUES, Message


def format_messages(
    messages: List[Union[dict, Message]], supports_images: bool = False
) -> List[dict]:
    """Format messages for LLM by converting them to OpenAI message format.

    Args:
        messages: List of messages that can be either dict or Message objects
        supports_images: Flag indicating if the target model supports image inputs

    Returns:
        List[dict]: List of formatted messages in OpenAI format

    Raises:
        ValueError: If messages are invalid or missing required fields
        TypeError: If unsupported message types are provided

    Examples:
        >>> msgs = [
        ...     Message.system_message("You are a helpful assistant"),
        ...     {"role": "user", "content": "Hello"},
        ...     Message.user_message("How are you?")
        ... ]
        >>> formatted = format_messages(msgs)
    """
    formatted_messages = []

    for message in messages:
        # Convert Message objects to dictionaries
        if isinstance(message, Message):
            message = message.to_dict()

        if isinstance(message, dict):
            # If message is a dict, ensure it has required fields
            if "role" not in message:
                raise ValueError("Message dict must contain 'role' field")

            # Process base64 images if present and model supports images
            if supports_images and message.get("base64_image"):
                # Initialize or convert content to appropriate format
                if not message.get("content"):
                    message["content"] = []
                elif isinstance(message["content"], str):
                    message["content"] = [
                        {"type": "text", "text": message["content"]}
                    ]
                elif isinstance(message["content"], list):
                    # Convert string items to proper text objects
                    message["content"] = [
                        (
                            {"type": "text", "text": item}
                            if isinstance(item, str)
                            else item
                        )
                        for item in message["content"]
                    ]

                # Add the image to content
                message["content"].append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{message['base64_image']}"
                        },
                    }
                )

                # Remove the base64_image field
                del message["base64_image"]
            # If model doesn't support images but message has base64_image, handle gracefully
            elif not supports_images and message.get("base64_image"):
                # Just remove the base64_image field and keep the text content
                del message["base64_image"]

            if "content" in message or "tool_calls" in message:
                formatted_messages.append(message)
            # else: do not include the message
        else:
            raise TypeError(f"Unsupported message type: {type(message)}")

    # Validate all messages have required fields
    for msg in formatted_messages:
        if msg["role"] not in ROLE_VALUES:
            raise ValueError(f"Invalid role: {msg['role']}")

    return formatted_messages
