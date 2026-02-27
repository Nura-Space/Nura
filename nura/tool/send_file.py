"""SendFile tool for sending files to the user via platform client."""
import os
import tempfile
import uuid

from loguru import logger

from nura.services.sendable import AudioContent, FileContent
from nura.services.utils import convert_to_opus, get_audio_duration
from nura.tool.base import BaseTool, ToolResult


def _get_client():
    """Get the current platform client."""
    from nura.services.base import ClientFactory
    client = ClientFactory.get_current_client()
    if not client:
        raise RuntimeError("No platform client configured. Call ClientFactory.set_current_platform() first.")
    return client


# Audio file types that should be sent as AudioContent
AUDIO_TYPES = ("opus", "mp3", "wav")


class SendFile(BaseTool):
    """Tool to send a file to the current user via platform client.

    Supports sending audio files (.wav, .mp3, .opus), video files (.mp4),
    and other file types. This tool is useful when skills produce output
    files that need to be delivered to the user, such as music-cover results.
    """

    name: str = "send_file"
    description: str = "发送文件给用户。支持音频(.wav, .mp3, .opus)、视频(.mp4)和其他文件类型。当技能生成了需要发送给用户的文件时使用。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要发送的文件的绝对路径",
            },
            "file_type": {
                "type": "string",
                "description": "文件类型，如 opus, mp3, wav, mp4, pdf, doc 等",
            },
        },
        "required": ["file_path", "file_type"],
    }

    def __init__(self):
        super().__init__()
        self._temp_files: list[str] = []

    def cleanup(self):
        """Clean up temporary files created during execution."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        self._temp_files.clear()

    async def execute(self, file_path: str, file_type: str) -> ToolResult:
        """Send a file to the user.

        Args:
            file_path: Absolute path to the file
            file_type: File type (opus, mp3, wav, mp4, pdf, etc.)

        Returns:
            ToolResult with success or error message
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return self.fail_response(f"文件不存在: {file_path}")

        client = _get_client()
        file_name = os.path.basename(file_path)
        sendable = None

        # Handle audio files specially
        if file_type.lower() in AUDIO_TYPES:
            # Get audio duration
            duration = await get_audio_duration(file_path)
            if duration is None:
                logger.warning(f"Failed to get audio duration, using 0")
                duration = 0
            logger.info(f"Got audio duration: {duration}ms for {file_name}")

            # Convert to opus if not already
            if file_type.lower() != "opus":
                temp_dir = tempfile.gettempdir()
                opus_path = os.path.join(temp_dir, f"{uuid.uuid4()}.opus")
                if await convert_to_opus(file_path, opus_path):
                    self._temp_files.append(opus_path)
                    sendable = AudioContent(
                        file_path=opus_path,
                        file_type="opus",
                        file_name=file_name,
                        duration=duration
                    )
                else:
                    logger.error("OPUS conversion failed")
                    return self.fail_response(f"音频格式转换失败")
            else:
                # Already opus, no conversion needed
                sendable = AudioContent(
                    file_path=file_path,
                    file_type="opus",
                    file_name=file_name,
                    duration=duration
                )
        else:
            # Non-audio files
            sendable = FileContent(
                file_path=file_path,
                file_type=file_type,
                file_name=file_name
            )

        if not sendable:
            return self.fail_response(f"无法创建发送内容")

        try:
            await client.send(sendable)
            logger.info(f"File sent to user: {file_name}")
            return self.success_response(f"文件已发送: {file_name}")
        except Exception as e:
            logger.error(f"SendFile failed: {e}")
            return self.fail_response(f"发送文件失败: {str(e)}")
        finally:
            self.cleanup()
