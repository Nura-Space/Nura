"""Tests for environment variable processing."""

import os
import pytest
from unittest.mock import patch

from nura.config.env import (
    parse_env_value,
    load_env_overrides,
    _process_nura_env,
    _process_platform_env,
)


@pytest.mark.unit
class TestParseEnvValue:
    """Tests for parse_env_value function."""

    def test_parse_bool_true(self):
        """Test parsing boolean true values."""
        assert parse_env_value("true") is True
        assert parse_env_value("True") is True
        assert parse_env_value("TRUE") is True
        assert parse_env_value("yes") is True
        assert parse_env_value("1") is True
        assert parse_env_value("on") is True

    def test_parse_bool_false(self):
        """Test parsing boolean false values."""
        assert parse_env_value("false") is False
        assert parse_env_value("False") is False
        assert parse_env_value("FALSE") is False
        assert parse_env_value("no") is False
        assert parse_env_value("0") is False
        assert parse_env_value("off") is False

    def test_parse_int(self):
        """Test parsing integer values."""
        assert parse_env_value("42") == 42
        assert parse_env_value("-10") == -10
        assert parse_env_value("0") is False  # Note: "0" is parsed as boolean False

    def test_parse_float(self):
        """Test parsing float values."""
        assert parse_env_value("3.14") == 3.14
        assert parse_env_value("-2.5") == -2.5

    def test_parse_string(self):
        """Test parsing string values."""
        assert parse_env_value("hello") == "hello"
        assert parse_env_value("sk-abc123") == "sk-abc123"


@pytest.mark.unit
class TestProcessNuraEnv:
    """Tests for _process_nura_env function."""

    def test_process_llm_env(self):
        """Test processing NURA_LLM_* environment variables."""
        overrides = {}
        _process_nura_env("NURA_LLM_API_KEY", "sk-test", overrides)
        _process_nura_env("NURA_LLM_MODEL", "gpt-4", overrides)
        _process_nura_env("NURA_LLM_MAX_TOKENS", "4096", overrides)

        assert overrides == {
            "llm": {
                "default": {
                    "api_key": "sk-test",
                    "model": "gpt-4",
                    "max_tokens": 4096,
                }
            }
        }

    def test_process_context_env(self):
        """Test processing NURA_CONTEXT_* environment variables."""
        overrides = {}
        _process_nura_env("NURA_CONTEXT_MAX_TOKENS", "128000", overrides)
        _process_nura_env("NURA_CONTEXT_KEEP_TURNS", "10", overrides)

        assert overrides == {
            "context": {
                "max_tokens": 128000,
                "keep_turns": 10,
            }
        }

    def test_process_memory_env(self):
        """Test processing NURA_MEMORY_* environment variables."""
        overrides = {}
        # NURA_MEMORY_DIR is mapped to memory.memory_dir via field_mappings
        _process_nura_env("NURA_MEMORY_DIR", "/path/to/memory", overrides)

        assert overrides == {
            "memory": {
                "memory_dir": "/path/to/memory",
            }
        }


@pytest.mark.unit
class TestProcessPlatformEnv:
    """Tests for _process_platform_env function."""

    def test_process_feishu_env(self):
        """Test processing FEISHU_* environment variables."""
        overrides = {}
        _process_platform_env("feishu", "FEISHU_APP_ID", "cli_xxx", overrides)
        _process_platform_env("feishu", "FEISHU_APP_SECRET", "secret_xxx", overrides)
        _process_platform_env("feishu", "FEISHU_ENABLE_VOICE_REPLY", "true", overrides)

        assert overrides == {
            "platforms": {
                "feishu": {
                    "app_id": "cli_xxx",
                    "app_secret": "secret_xxx",
                    "enable_voice_reply": True,
                }
            }
        }


@pytest.mark.unit
class TestLoadEnvOverrides:
    """Tests for load_env_overrides function."""

    @patch.dict(
        os.environ,
        {
            "NURA_LLM_API_KEY": "sk-test",
            "NURA_LLM_MODEL": "gpt-4",
            "NURA_CONTEXT_MAX_TOKENS": "128000",
            "FEISHU_APP_ID": "cli_xxx",
            "FEISHU_APP_SECRET": "secret_xxx",
        },
        clear=False,
    )
    def test_load_all_overrides(self):
        """Test loading all environment variable overrides."""
        overrides = load_env_overrides()

        assert "llm" in overrides
        assert overrides["llm"]["default"]["api_key"] == "sk-test"
        assert overrides["llm"]["default"]["model"] == "gpt-4"

        assert "context" in overrides
        assert overrides["context"]["max_tokens"] == 128000

        assert "platforms" in overrides
        assert overrides["platforms"]["feishu"]["app_id"] == "cli_xxx"
        assert overrides["platforms"]["feishu"]["app_secret"] == "secret_xxx"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_empty_overrides(self):
        """Test loading with no environment variables."""
        overrides = load_env_overrides()

        assert overrides == {}
