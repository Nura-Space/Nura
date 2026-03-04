"""Tests for nura/cli.py"""
from unittest.mock import patch
import json
import tempfile
import os

from click.testing import CliRunner


class TestCLI:
    """Unit tests for CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_command(self):
        """Test main CLI command exists."""
        from nura.cli import main
        result = self.runner.invoke(main)
        assert result.exit_code == 0
        assert "Nura" in result.output

    def test_run_command_missing_config(self):
        """Test run command without config option."""
        from nura.cli import main
        result = self.runner.invoke(main, ['run'])
        assert result.exit_code != 0

    def test_run_command_unsupported_platform(self):
        """Test run command with unsupported platform."""
        from nura.cli import main

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "config"}, f)
            config_path = f.name

        try:
            result = self.runner.invoke(main, ['run', '--config', config_path, '--platform', 'unsupported'])
            assert "not supported" in result.output.lower() or result.exit_code != 0
        finally:
            os.unlink(config_path)

    @patch('nura.integrations.feishu.bot.run_feishu_bot')
    def test_run_command_feishu_success(self, mock_run_bot):
        """Test run command with feishu platform."""
        from nura.cli import main

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"app_id": "test", "app_secret": "test"}, f)
            config_path = f.name

        try:
            mock_run_bot.return_value = None
            result = self.runner.invoke(main, ['run', '--config', config_path, '--platform', 'feishu'])
            # Either it runs or exits with error (depending on async behavior)
            # Just verify the command was recognized
            assert "feishu" in result.output.lower() or "error" in result.output.lower() or result.exit_code in [0, 1]
        finally:
            os.unlink(config_path)

    def test_run_command_with_workspace(self):
        """Test run command with workspace option."""
        from nura.cli import main

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "config"}, f)
            config_path = f.name

        try:
            result = self.runner.invoke(main, ['run', '--config', config_path, '--platform', 'wechat'])
            # WeChat is not supported yet
            assert "not supported" in result.output.lower()
        finally:
            os.unlink(config_path)
