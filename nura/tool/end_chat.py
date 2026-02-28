"""EndChat tool for ending the conversation with the user."""

from nura.tool.base import BaseTool, ToolResult
from loguru import logger

_ENDCHAT_DESCRIPTION = """End the current chat session with the user.
Use this tool when the conversation is complete or the user indicates they want to end the chat.
The agent will stop processing further messages in this session."""


class EndChat(BaseTool):
    """Tool to end the current chat session with the user.

    This tool explicitly ends the conversation, signaling to the agent
    that no further responses are needed for the current session.
    """

    name: str = "end_chat"
    description: str = _ENDCHAT_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Optional reason for ending the chat (e.g., 'user said goodbye', 'task completed').",
            }
        },
        "required": [],
    }

    async def execute(self, reason: str = None) -> ToolResult:
        """End the current chat session.

        Args:
            reason: Optional reason for ending the chat

        Returns:
            ToolResult confirming the chat has ended
        """
        if reason:
            logger.info(f"Ending chat session. Reason: {reason}")
            return self.success_response(f"Chat session ended. Reason: {reason}")
        else:
            logger.info("Ending chat session")
            return self.success_response("Chat session has ended")
