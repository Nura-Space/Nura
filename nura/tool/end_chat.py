"""EndChat tool for ending the conversation with the user."""

from nura.tool.base import BaseTool, ToolResult
from nura.core.logger import logger

_ENDCHAT_DESCRIPTION = """结束当前对话轮次。在以下情况下必须调用：
1. 每次通过 send_message 发送回复后，立即调用以结束本轮处理
2. 用户明确表示结束对话（如说再见）
3. 任务已完成，无需进一步响应

调用后 agent 将停止处理，等待用户的下一条消息。"""


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
