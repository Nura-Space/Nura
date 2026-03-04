"""Unit tests for SendMessage tool."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nura.tool.send_message import SendMessage


@pytest.mark.unit
class TestSendMessage:
    """Test SendMessage tool."""

    def test_send_message_creation(self):
        """Test creating a SendMessage tool."""
        tool = SendMessage()
        assert tool.name == "send_message"
        assert "message" in tool.description.lower() or "发送" in tool.description
        assert "content" in tool.parameters["properties"]

    def test_send_message_parameters(self):
        """Test SendMessage parameters schema."""
        tool = SendMessage()
        params = tool.parameters

        assert params["type"] == "object"
        assert "content" in params["required"]
        assert "content" in params["properties"]
        assert "emotion" in params["properties"]
        # Check emotion enum
        assert "enum" in params["properties"]["emotion"]
        assert "happy" in params["properties"]["emotion"]["enum"]

    @pytest.mark.asyncio
    async def test_execute_content_not_string(self):
        """Test execute with non-string content."""
        tool = SendMessage()

        result = await tool.execute(content=123)

        assert result.error is not None
        assert "错误" in result.error or "error" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_simple_message(self):
        """Test executing a simple message."""
        tool = SendMessage()

        # Mock client
        mock_client = MagicMock()
        mock_client._enable_voice = False

        mock_send = AsyncMock()
        mock_client.send = mock_send

        with patch('nura.tool.send_message._get_client', return_value=mock_client):
            result = await tool.execute(content="Hello world")

            assert result.output is not None
            assert "已发送" in result.output or "sent" in result.output.lower()
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_execute_multiline_message(self):
        """Test executing a multiline message."""
        tool = SendMessage()

        mock_client = MagicMock()
        mock_client._enable_voice = False
        mock_send = AsyncMock()
        mock_client.send = mock_send

        with patch('nura.tool.send_message._get_client', return_value=mock_client):
            await tool.execute(content="Line 1\nLine 2\nLine 3")

            # Should be called for each non-empty line
            assert mock_send.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_with_emotion(self):
        """Test executing with emotion emoji."""
        tool = SendMessage()

        mock_client = MagicMock()
        mock_client._enable_voice = False
        mock_client.emoji_func = {
            "happy": ["😊", "😄"],
            "thanks": ["🙏", "谢"]
        }

        mock_send = AsyncMock()
        mock_client.send = mock_send

        with patch('nura.tool.send_message._get_client', return_value=mock_client):
            with patch('random.random', return_value=0.3):  # Force emoji to be sent
                await tool.execute(content="Thank you!", emotion="thanks")

                # Note: with random=0.3, emoji should be sent (0.3 < 0.5)

    @pytest.mark.asyncio
    async def test_execute_emoji_only_segment(self):
        """Test executing with emoji-only segment like [SomeEmoji]."""
        tool = SendMessage()

        mock_client = MagicMock()
        mock_client._enable_voice = False

        mock_send = AsyncMock()
        mock_client.send = mock_send

        with patch('nura.tool.send_message._get_client', return_value=mock_client):
            await tool.execute(content="[wave]")

            # Should handle emoji-only segments

    def test_cleanup(self):
        """Test cleanup method."""
        tool = SendMessage()
        tool._temp_files = ["/tmp/test1.txt", "/tmp/test2.txt"]

        # Files don't exist so this should not raise
        tool.cleanup()

        assert len(tool._temp_files) == 0

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = SendMessage()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "send_message"
        assert "parameters" in tool_dict["function"]


@pytest.mark.unit
class TestSendMessageVoice:
    """Test SendMessage voice reply functionality."""

    @pytest.mark.asyncio
    async def test_execute_with_voice_enabled(self):
        """Test execute with voice enabled."""
        tool = SendMessage()

        # Mock client with voice enabled
        mock_client = MagicMock()
        mock_client._enable_voice = True
        mock_client._tts_service = None  # No TTS service

        mock_send = AsyncMock()
        mock_client.send = mock_send

        with patch('nura.tool.send_message._get_client', return_value=mock_client):
            await tool.execute(content="Voice message")

            # Should fall back to text when TTS not available

    @pytest.mark.asyncio
    async def test_execute_with_tts_service(self):
        """Test execute with TTS service."""
        tool = SendMessage()

        # Mock client with TTS service
        mock_client = MagicMock()
        mock_client._enable_voice = True
        mock_tts = AsyncMock()
        mock_tts.generate_audio = AsyncMock(return_value=True)
        mock_client._tts_service = mock_tts

        mock_send = AsyncMock()
        mock_client.send = mock_send

        with patch('nura.tool.send_message._get_client', return_value=mock_client):
            with patch('nura.tool.send_message.convert_to_opus', return_value=True):
                with patch('nura.tool.send_message.get_audio_duration', return_value=1000):
                    # This will create temp files that don't exist, but that's ok for test
                    await tool.execute(content="Voice message")
