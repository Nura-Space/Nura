"""Message tool for sending messages to the user."""
import os
import re
import tempfile
import uuid

from loguru import logger

from nura.tool.base import BaseTool, ToolResult
from nura.services.sendable import AudioContent, TextContent
from nura.services.utils import convert_to_opus, get_audio_duration


def _get_client():
    """Get the current platform client."""
    from nura.services.base import ClientFactory
    client = ClientFactory.get_current_client()
    if not client:
        raise RuntimeError("No platform client configured. Call ClientFactory.set_current_platform() first.")
    return client


class SendMessage(BaseTool):
    """Tool to send a message to the current user.

    This tool allows the agent to directly send a message to the user,
    separate from the final response generation. Optionally add emoji based on emotion.

    The message is sent directly via the platform client, which handles:
    - Segmentation by newlines
    - Emoji pattern detection
    - Voice reply via TTS (if enabled)
    """

    name: str = "send_message"
    description: str = "发送消息给用户。可选添加emoji表情，根据消息情感选择合适的类型。"
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "消息内容",
            },
            "emotion": {
                "type": "string",
                "description": "情感类型，根据消息内容选择：happy(开心)、thanks(感谢)、goodbye(再见)、excited(兴奋)、thinking(思考)、sad(悲伤)、agree(同意)、greeting(问候)、encourage(鼓励)、surprise(惊讶)、waiting(等待)、working(工作中)、eating(餐饮)、travel(出行)、holiday(节日)、disagree(不同意)。不指定时默认不加表情。",
                "enum": ["happy", "thanks", "goodbye", "excited", "thinking", "sad", "agree", "greeting", "encourage", "surprise", "waiting", "working", "eating", "travel", "holiday", "disagree"]
            }
        },
        "required": ["content"],
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

    async def execute(self, content: str, emotion: str = None) -> ToolResult:
        """Send a message to the user.

        Args:
            content: The message content to send
            emotion: Optional emotion type to add emoji

        Returns:
            ToolResult with success or error message
        """
        if not isinstance(content, str):
            logger.warning(f"Message format is not String, {type(content)}")
            return self.fail_response(f"消息格式错误，不是字符串: {type(content)}")

        client = _get_client()

        # Determine if voice reply should be used
        enable_voice = getattr(client, '_enable_voice', False)

        # Split by newline and process each segment
        segments = content.split("\n")
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            # Check if this is an emoji-only segment like [SomeEmoji]
            if re.match(r'^\[.+\]$', segment):
                text_content = TextContent(text=segment)
                await client.send(text_content)
            elif enable_voice:
                # Use voice reply for this segment
                await self._send_voice(segment)
            else:
                text_content = TextContent(text=segment)
                await client.send(text_content)

        # Send emotion emoji as separate message (50% probability)
        if emotion and hasattr(client, 'emoji_func'):
            import random
            if emotion in client.emoji_func and random.random() > 0.5:
                emoji_text = random.choice(client.emoji_func[emotion])
                text_content = TextContent(text=emoji_text)
                await client.send(text_content)
                logger.info(f"Adding emoji {emoji_text} for emotion: {emotion}")

        self.cleanup()
        return self.success_response(f"消息已发送: {content}")

    async def _send_voice(self, text: str):
        """Send voice reply using TTS."""
        client = _get_client()
        tts_service = getattr(client, '_tts_service', None)
        if not tts_service:
            # Fallback to text if TTS not available
            text_content = TextContent(text=text)
            await client.send(text_content)
            return

        try:
            # 1. Generate MP3
            temp_dir = tempfile.gettempdir()
            mp3_path = f"{temp_dir}/reply_{uuid.uuid4()}.mp3"
            self._temp_files.append(mp3_path)

            if not await tts_service.generate_audio(text, mp3_path):
                logger.error("TTS failed, falling back to text")
                text_content = TextContent(text=text)
                await client.send(text_content)
                return

            # 2. Convert to OPUS
            opus_path = mp3_path.replace(".mp3", ".opus")
            if not await convert_to_opus(mp3_path, opus_path):
                logger.error("OPUS conversion failed, falling back to text")
                text_content = TextContent(text=text)
                await client.send(text_content)
                return

            self._temp_files.append(opus_path)

            # 3. Get duration and create AudioContent
            duration = await get_audio_duration(opus_path)
            if duration is None:
                duration = 0
            logger.info(f"Got audio duration: {duration}ms for voice reply")

            audio_content = AudioContent(
                file_path=opus_path,
                file_type="opus",
                duration=duration
            )

            await client.send(audio_content)

        except Exception as e:
            logger.error(f"Voice reply failed: {e}")
            text_content = TextContent(text=text)
            await client.send(text_content)
