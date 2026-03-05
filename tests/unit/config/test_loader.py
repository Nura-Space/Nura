"""Tests for configuration loader module."""

import pytest

from nura.config.loader import (
    load_toml,
    load_json,
    load_yaml,
    deep_merge,
    load_config_file,
)


@pytest.mark.unit
class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}
        # Ensure original dicts are unchanged
        assert base == {"a": 1, "b": 2}
        assert override == {"b": 3, "c": 4}

    def test_nested_merge(self):
        """Test nested dictionary merge."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"d": 4, "e": 5}, "f": 6}
        result = deep_merge(base, override)

        assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}

    def test_deep_nested_merge(self):
        """Test deeply nested dictionary merge."""
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"d": 3, "e": 4}}}
        result = deep_merge(base, override)

        assert result == {"a": {"b": {"c": 1, "d": 3, "e": 4}}}

    def test_override_with_non_dict(self):
        """Test overriding dict with non-dict value."""
        base = {"a": {"b": 1}}
        override = {"a": "string"}
        result = deep_merge(base, override)

        assert result == {"a": "string"}


@pytest.mark.unit
class TestLoadToml:
    """Tests for load_toml function."""

    def test_load_valid_toml(self, tmp_path):
        """Test loading valid TOML file."""
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
[section]
key = "value"
number = 42
        """)

        result = load_toml(toml_file)
        assert result == {"section": {"key": "value", "number": 42}}

    def test_load_nonexistent_toml(self, tmp_path):
        """Test loading nonexistent TOML file."""
        toml_file = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            load_toml(toml_file)

    def test_load_invalid_toml(self, tmp_path):
        """Test loading invalid TOML file."""
        toml_file = tmp_path / "invalid.toml"
        toml_file.write_text("[invalid toml content")

        with pytest.raises(ValueError):
            load_toml(toml_file)


@pytest.mark.unit
class TestLoadJson:
    """Tests for load_json function."""

    def test_load_valid_json(self, tmp_path):
        """Test loading valid JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value", "number": 42}')

        result = load_json(json_file)
        assert result == {"key": "value", "number": 42}

    def test_load_nonexistent_json(self, tmp_path):
        """Test loading nonexistent JSON file."""
        json_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_json(json_file)

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json")

        with pytest.raises(ValueError):
            load_json(json_file)


@pytest.mark.unit
class TestLoadYaml:
    """Tests for load_yaml function."""

    def test_load_valid_yaml(self, tmp_path):
        """Test loading valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
key: value
number: 42
        """)

        result = load_yaml(yaml_file)
        assert result == {"key": "value", "number": 42}

    def test_load_nonexistent_yaml(self, tmp_path):
        """Test loading nonexistent YAML file."""
        yaml_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_yaml(yaml_file)


@pytest.mark.unit
class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_load_toml_file(self, tmp_path):
        """Test loading TOML file by extension."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('[section]\nkey = "value"')

        result = load_config_file(config_file)
        assert result == {"section": {"key": "value"}}

    def test_load_json_file(self, tmp_path):
        """Test loading JSON file by extension."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')

        result = load_config_file(config_file)
        assert result == {"key": "value"}

    def test_load_yaml_file(self, tmp_path):
        """Test loading YAML file by extension."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value")

        result = load_config_file(config_file)
        assert result == {"key": "value"}

    def test_unsupported_extension(self, tmp_path):
        """Test loading file with unsupported extension."""
        config_file = tmp_path / "config.txt"
        config_file.write_text("some content")

        with pytest.raises(ValueError, match="Unsupported config file extension"):
            load_config_file(config_file)
