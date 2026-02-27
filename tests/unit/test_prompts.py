"""Tests for prompt module."""
import os
import tempfile

import pytest
import yaml

from nura.prompts import (
    load_prompt,
    load_prompt_with_context,
    build_roleplay_prompt,
)


class TestLoadPrompt:
    """Tests for load_prompt function."""

    @pytest.mark.unit
    def test_load_zh_prompt(self):
        """Test loading Chinese prompt template."""
        template = load_prompt("roleplay", "zh")
        assert template is not None
        assert len(template) > 0
        assert "{name}" in template

    @pytest.mark.unit
    def test_load_en_prompt(self):
        """Test loading English prompt template."""
        template = load_prompt("roleplay", "en")
        assert template is not None
        assert len(template) > 0
        assert "{name}" in template

    @pytest.mark.unit
    def test_load_nonexistent_template(self):
        """Test loading non-existent template raises error."""
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent", "zh")

    @pytest.mark.unit
    def test_load_nonexistent_language(self):
        """Test loading non-existent language falls back correctly."""
        # Should try to load nonexistent_zh.yaml which doesn't exist
        with pytest.raises(FileNotFoundError):
            load_prompt("roleplay", "fr")


class TestLoadPromptWithContext:
    """Tests for load_prompt_with_context function."""

    @pytest.mark.unit
    def test_load_with_context(self):
        """Test loading prompt with context."""
        context = {
            "name": "TestBot",
            "description": "A test bot",
            "style": "Friendly",
            "world": "Modern",
            "relations": "Friend",
            "notes": "Test notes"
        }

        result = load_prompt_with_context("roleplay", context, "zh")

        assert "TestBot" in result
        assert "A test bot" in result
        assert "Friendly" in result

    @pytest.mark.unit
    def test_load_with_missing_context_key(self):
        """Test loading with missing context key raises error."""
        context = {"name": "Test"}  # Missing other keys

        # Should raise KeyError because template requires all keys
        with pytest.raises(KeyError):
            load_prompt_with_context("roleplay", context, "en")


class TestBuildRoleplayPrompt:
    """Tests for build_roleplay_prompt function."""

    @pytest.mark.unit
    def test_build_from_profile(self):
        """Test building prompt from profile YAML."""
        profile = {
            "name": "Alice",
            "description": "A friendly assistant",
            "style": "Casual and friendly",
            "world": "Tech startup",
            "relations": "Colleague",
            "notes": "Loves coffee",
            "language": "zh"
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            yaml.dump(profile, f)
            profile_path = f.name

        try:
            result = build_roleplay_prompt(profile_path)

            assert "Alice" in result
            assert "A friendly assistant" in result
            assert "Casual and friendly" in result
        finally:
            os.unlink(profile_path)

    @pytest.mark.unit
    def test_build_with_en_language(self):
        """Test building prompt with English language."""
        profile = {
            "name": "Bob",
            "description": "Helpful assistant",
            "style": "Professional",
            "world": "Office",
            "relations": "Colleague",
            "notes": "",
            "language": "en"
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            yaml.dump(profile, f)
            profile_path = f.name

        try:
            result = build_roleplay_prompt(profile_path)

            assert "Bob" in result
            assert "Helpful assistant" in result
        finally:
            os.unlink(profile_path)

    @pytest.mark.unit
    def test_build_nonexistent_file(self):
        """Test building prompt from non-existent file."""
        result = build_roleplay_prompt("/nonexistent/path.yaml")

        assert result == ""

    @pytest.mark.unit
    def test_build_sets_env_variable(self):
        """Test that env variable is set."""
        profile = {
            "name": "TestBot",
            "description": "Test",
            "style": "Test",
            "world": "",
            "relations": "",
            "notes": "",
            "language": "zh"
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            yaml.dump(profile, f)
            profile_path = f.name

        try:
            build_roleplay_prompt(profile_path)

            assert os.environ.get("VIRTUAL_IP_NAME") == "TestBot"
        finally:
            os.unlink(profile_path)

    @pytest.mark.unit
    def test_build_with_defaults(self):
        """Test building prompt with minimal profile."""
        profile = {
            "name": "DefaultBot"
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            yaml.dump(profile, f)
            profile_path = f.name

        try:
            result = build_roleplay_prompt(profile_path)

            assert "DefaultBot" in result
        finally:
            os.unlink(profile_path)
