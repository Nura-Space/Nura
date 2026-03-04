"""Tests for nura/services/utils.py"""

import pytest
from unittest.mock import patch, AsyncMock

from nura.services import utils


class TestConvertToOpus:
    """Unit tests for convert_to_opus function."""

    @pytest.mark.asyncio
    async def test_convert_to_opus_success(self):
        """Test successful MP3 to OPUS conversion."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Mock successful process
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(b"Conversion complete", b"")
            )
            mock_exec.return_value = mock_process

            result = await utils.convert_to_opus("/input/test.mp3", "/output/test.opus")

            assert result == "/output/test.opus"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_to_opus_default_output(self):
        """Test conversion with default output path."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(b"Conversion complete", b"")
            )
            mock_exec.return_value = mock_process

            result = await utils.convert_to_opus("/input/test.mp3")

            assert result == "output.opus"

    @pytest.mark.asyncio
    async def test_convert_to_opus_ffmpeg_failure(self):
        """Test conversion when ffmpeg returns non-zero."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"ffmpeg error"))
            mock_exec.return_value = mock_process

            result = await utils.convert_to_opus("/input/test.mp3", "/output/test.opus")

            assert result is None

    @pytest.mark.asyncio
    async def test_convert_to_opus_exception(self):
        """Test conversion when exception occurs."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.side_effect = FileNotFoundError("ffmpeg not found")

            result = await utils.convert_to_opus("/input/test.mp3", "/output/test.opus")

            assert result is None


class TestGetAudioDuration:
    """Unit tests for get_audio_duration function."""

    @pytest.mark.asyncio
    async def test_get_audio_duration_success(self):
        """Test successful audio duration retrieval."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"10.5", b""))
            mock_exec.return_value = mock_process

            result = await utils.get_audio_duration("/input/test.opus")

            assert result == 10500  # 10.5 seconds = 10500 milliseconds

    @pytest.mark.asyncio
    async def test_get_audio_duration_zero_duration(self):
        """Test audio duration with zero duration."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"0", b""))
            mock_exec.return_value = mock_process

            result = await utils.get_audio_duration("/input/test.opus")

            assert result == 0

    @pytest.mark.asyncio
    async def test_get_audio_duration_fractional(self):
        """Test audio duration with fractional seconds."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"3.14159", b""))
            mock_exec.return_value = mock_process

            result = await utils.get_audio_duration("/input/test.opus")

            assert result == 3141  # 3.14159 seconds = 3141 milliseconds (truncated)

    @pytest.mark.asyncio
    async def test_get_audio_duration_ffprobe_failure(self):
        """Test when ffprobe returns non-zero."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"ffprobe error"))
            mock_exec.return_value = mock_process

            result = await utils.get_audio_duration("/input/test.opus")

            assert result == 0

    @pytest.mark.asyncio
    async def test_get_audio_duration_invalid_float(self):
        """Test when ffprobe returns invalid float."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"not_a_number", b""))
            mock_exec.return_value = mock_process

            result = await utils.get_audio_duration("/input/test.opus")

            assert result == 0

    @pytest.mark.asyncio
    async def test_get_audio_duration_exception(self):
        """Test when exception occurs."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.side_effect = FileNotFoundError("ffprobe not found")

            result = await utils.get_audio_duration("/input/test.opus")

            assert result == 0
