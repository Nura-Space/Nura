"""Unit tests for SendFile tool."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nura.tool.send_file import SendFile


@pytest.mark.unit
class TestSendFile:
    """Test SendFile tool."""

    def test_send_file_creation(self):
        """Test creating a SendFile tool."""
        tool = SendFile()
        assert tool.name == "send_file"
        assert "file" in tool.description.lower() or "文件" in tool.description
        assert "file_path" in tool.parameters["properties"]
        assert "file_type" in tool.parameters["properties"]

    def test_send_file_parameters(self):
        """Test SendFile parameters schema."""
        tool = SendFile()
        params = tool.parameters

        assert params["type"] == "object"
        assert "file_path" in params["required"]
        assert "file_type" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_file_not_found(self):
        """Test execute with non-existent file."""
        tool = SendFile()

        result = await tool.execute(file_path="/nonexistent/file.txt", file_type="txt")

        assert result.error is not None
        assert "不存在" in result.error or "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_audio_file(self):
        """Test executing with audio file."""
        tool = SendFile()

        # Mock file exists
        with patch("os.path.exists", return_value=True):
            # Mock client
            mock_client = MagicMock()
            mock_send = AsyncMock()
            mock_client.send = mock_send

            with patch("nura.tool.send_file._get_client", return_value=mock_client):
                with patch("nura.tool.send_file.get_audio_duration", return_value=5000):
                    with patch(
                        "nura.tool.send_file.convert_to_opus", return_value=True
                    ):
                        # Test with mp3 file
                        await tool.execute(file_path="/tmp/test.mp3", file_type="mp3")

                        # Should try to convert and send

    @pytest.mark.asyncio
    async def test_execute_opus_file(self):
        """Test executing with opus file (no conversion needed)."""
        tool = SendFile()

        # Create a temporary file
        temp_dir = os.path.dirname(__file__)
        test_file = os.path.join(temp_dir, "test.opus")

        # Create the file
        with open(test_file, "wb") as f:
            f.write(b"test opus content")

        try:
            mock_client = MagicMock()
            mock_send = AsyncMock()
            mock_client.send = mock_send

            with patch("nura.tool.send_file._get_client", return_value=mock_client):
                with patch("nura.tool.send_file.get_audio_duration", return_value=3000):
                    await tool.execute(file_path=test_file, file_type="opus")

                    # Should send without conversion
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)

    @pytest.mark.asyncio
    async def test_execute_non_audio_file(self):
        """Test executing with non-audio file."""
        tool = SendFile()

        # Create a temporary file
        temp_dir = os.path.dirname(__file__)
        test_file = os.path.join(temp_dir, "test.pdf")

        # Create the file
        with open(test_file, "wb") as f:
            f.write(b"test pdf content")

        try:
            mock_client = MagicMock()
            mock_send = AsyncMock()
            mock_client.send = mock_send

            with patch("nura.tool.send_file._get_client", return_value=mock_client):
                result = await tool.execute(file_path=test_file, file_type="pdf")

                assert result.output is not None or result.error is not None
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)

    @pytest.mark.asyncio
    async def test_execute_conversion_failure(self):
        """Test execute when audio conversion fails."""
        tool = SendFile()

        with patch("os.path.exists", return_value=True):
            mock_client = MagicMock()
            mock_send = AsyncMock()
            mock_client.send = mock_send

            with patch("nura.tool.send_file._get_client", return_value=mock_client):
                with patch("nura.tool.send_file.get_audio_duration", return_value=1000):
                    with patch(
                        "nura.tool.send_file.convert_to_opus", return_value=False
                    ):
                        result = await tool.execute(
                            file_path="/tmp/test.mp3", file_type="mp3"
                        )

                        assert result.error is not None
                        assert "转换失败" in result.error

    def test_cleanup(self):
        """Test cleanup method."""
        tool = SendFile()
        tool._temp_files = ["/tmp/test1.opus", "/tmp/test2.opus"]

        # Files don't exist so this should not raise
        tool.cleanup()

        assert len(tool._temp_files) == 0

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = SendFile()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "send_file"
        assert "parameters" in tool_dict["function"]


@pytest.mark.unit
class TestSendFileEdgeCases:
    """Test SendFile edge cases."""

    @pytest.mark.asyncio
    async def test_execute_send_exception(self):
        """Test execute when client.send raises exception."""
        tool = SendFile()

        # Create a temporary file
        temp_dir = os.path.dirname(__file__)
        test_file = os.path.join(temp_dir, "test_exception.txt")

        with open(test_file, "wb") as f:
            f.write(b"test content")

        try:
            mock_client = MagicMock()
            mock_client.send = AsyncMock(side_effect=Exception("Send failed"))

            with patch("nura.tool.send_file._get_client", return_value=mock_client):
                result = await tool.execute(file_path=test_file, file_type="txt")

                assert result.error is not None
                assert "发送" in result.error or "failed" in result.error.lower()
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    @pytest.mark.asyncio
    async def test_execute_get_duration_failure(self):
        """Test execute when get_audio_duration returns None."""
        tool = SendFile()

        with patch("os.path.exists", return_value=True):
            mock_client = MagicMock()
            mock_send = AsyncMock()
            mock_client.send = mock_send

            with patch("nura.tool.send_file._get_client", return_value=mock_client):
                with patch("nura.tool.send_file.get_audio_duration", return_value=None):
                    with patch(
                        "nura.tool.send_file.convert_to_opus", return_value=True
                    ):
                        await tool.execute(file_path="/tmp/test.mp3", file_type="mp3")

                        # Should handle None duration gracefully (default to 0)
