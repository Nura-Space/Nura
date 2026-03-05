"""Tests for TTS service module."""

import pytest
from unittest.mock import MagicMock, patch
import base64
import json

from nura.services.tts_service import VolcengineTTS


class TestVolcengineTTS:
    """Test cases for VolcengineTTS."""

    @pytest.fixture
    def tts_config(self):
        """Create TTS configuration."""
        return {
            "tts_config": {
                "appid": "test_app_id",
                "access_token": "test_token",
                "cluster": "test_cluster",
                "voice_type": "test_voice",
                "api_url": "https://test-api.example.com/tts",
            }
        }

    @pytest.mark.unit
    def test_initialization(self, tts_config):
        """Test TTS service initialization."""
        tts = VolcengineTTS(tts_config)

        assert tts.appid == "test_app_id"
        assert tts.access_token == "test_token"
        assert tts.cluster == "test_cluster"
        assert tts.voice_type == "test_voice"
        assert tts.api_url == "https://test-api.example.com/tts"
        assert "Bearer" in tts.header["Authorization"]

    @pytest.mark.unit
    def test_initialization_minimal(self):
        """Test TTS service with minimal config."""
        tts = VolcengineTTS({})

        assert tts.appid is None
        assert tts.access_token is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_success(self, tts_config, tmp_path):
        """Test successful audio generation."""
        tts = VolcengineTTS(tts_config)

        # Create mock response with audio data
        mock_audio_data = b"fake_audio_data"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": base64.b64encode(mock_audio_data).decode("utf-8")
        }

        output_file = tmp_path / "output.mp3"

        with patch(
            "nura.services.tts_service.requests.post", return_value=mock_response
        ):
            result = await tts.generate_audio("Hello world", str(output_file))

        assert result is not None
        assert str(output_file) == result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_api_error(self, tts_config):
        """Test audio generation with API error."""
        tts = VolcengineTTS(tts_config)

        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "some error"}

        with patch(
            "nura.services.tts_service.requests.post", return_value=mock_response
        ):
            result = await tts.generate_audio("Hello world")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_network_error(self, tts_config):
        """Test audio generation with network error."""
        import requests

        tts = VolcengineTTS(tts_config)

        with patch(
            "nura.services.tts_service.requests.post",
            side_effect=requests.RequestException("Network error"),
        ):
            result = await tts.generate_audio("Hello world")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_invalid_response(self, tts_config):
        """Test audio generation with invalid JSON response."""
        tts = VolcengineTTS(tts_config)

        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with patch(
            "nura.services.tts_service.requests.post", return_value=mock_response
        ):
            result = await tts.generate_audio("Hello world")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_default_output_path(self, tts_config):
        """Test audio generation with default output path."""
        tts = VolcengineTTS(tts_config)

        mock_audio_data = b"fake_audio_data"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": base64.b64encode(mock_audio_data).decode("utf-8")
        }

        with patch(
            "nura.services.tts_service.requests.post", return_value=mock_response
        ):
            result = await tts.generate_audio("Hello world")

        assert result == "output.mp3"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_empty_data(self, tts_config):
        """Test audio generation with empty data in response."""
        tts = VolcengineTTS(tts_config)

        mock_response = MagicMock()
        mock_response.json.return_value = {}  # No data field

        with patch(
            "nura.services.tts_service.requests.post", return_value=mock_response
        ):
            result = await tts.generate_audio("Hello world")

        assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audio_file_write_error(self, tts_config):
        """Test audio generation with file write error."""
        tts = VolcengineTTS(tts_config)

        mock_audio_data = b"fake_audio_data"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": base64.b64encode(mock_audio_data).decode("utf-8")
        }

        # Try to write to an invalid path
        with patch(
            "nura.services.tts_service.requests.post", return_value=mock_response
        ):
            result = await tts.generate_audio("Hello world", "/invalid/path/output.mp3")

        assert result is None
