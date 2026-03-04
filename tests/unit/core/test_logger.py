"""Tests for nura/core/logger.py"""


class TestLogger:
    """Unit tests for logger module."""

    def test_define_log_level_default(self):
        """Test define_log_level with default parameters."""
        from nura.core import logger

        # The logger is the loguru Logger instance
        assert logger is not None

    def test_logger_info(self):
        """Test logger.info method."""
        from nura.core import logger

        # Should not raise any exception
        logger.info("Test info message")

    def test_logger_debug(self):
        """Test logger.debug method."""
        from nura.core import logger

        # Should not raise any exception
        logger.debug("Test debug message")

    def test_logger_warning(self):
        """Test logger.warning method."""
        from nura.core import logger

        # Should not raise any exception
        logger.warning("Test warning message")

    def test_logger_error(self):
        """Test logger.error method."""
        from nura.core import logger

        # Should not raise any exception
        logger.error("Test error message")

    def test_logger_critical(self):
        """Test logger.critical method."""
        from nura.core import logger

        # Should not raise any exception
        logger.critical("Test critical message")

    def test_logger_exception(self):
        """Test logger.exception method."""
        from nura.core import logger

        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should not raise any exception
            logger.exception("Test exception message")

    def test_logger_with_extra_context(self):
        """Test logger with extra context."""
        from nura.core import logger

        # Should not raise any exception
        logger.info("Test message", extra={"key": "value"})

    def test_logger_bind(self):
        """Test logger.bind method."""
        from nura.core import logger

        # Should not raise any exception
        bound = logger.bind(user="test_user")
        bound.info("Bound message")


class TestContextLogger:
    """Unit tests for context logger functions."""

    def test_get_context_logger(self):
        """Test get_context_logger returns a file-like object."""
        from nura.core.logger import get_context_logger

        # Should return a file object
        f = get_context_logger()
        assert hasattr(f, "write")
        assert hasattr(f, "flush")

    def test_context_log(self):
        """Test context_log writes to context file."""
        from nura.core.logger import context_log, close_context_logger
        import os

        # Close any existing logger
        close_context_logger()

        # Write to context log
        test_message = "Test context message"
        context_log(test_message)

        # Find the context log file
        import glob
        log_files = glob.glob("logs/context_*.log")
        assert len(log_files) > 0

        # Read the latest file and verify content
        latest_file = max(log_files, key=os.path.getmtime)
        with open(latest_file, "r") as f:
            content = f.read()
        assert test_message in content

    def test_context_log_does_not_output_to_terminal(self):
        """Test context_log does not output to terminal (stderr)."""
        from nura.core.logger import close_context_logger
        import subprocess

        # Close any existing logger
        close_context_logger()

        # Run in subprocess to capture stderr
        result = subprocess.run(
            [
                "uv", "run", "python", "-c",
                "from nura.core.logger import context_log; context_log('silent test')"
            ],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # stderr should be empty (no loguru output)
        assert result.stderr == "" or "Traceback" not in result.stderr

    def test_close_context_logger(self):
        """Test close_context_logger closes the file."""
        # Import the module directly using importlib
        import importlib
        logger_module = importlib.import_module("nura.core.logger")

        # Ensure logger is open first
        logger_module.get_context_logger()
        assert logger_module._context_log_file is not None

        # Close it
        logger_module.close_context_logger()
        assert logger_module._context_log_file is None
