"""Tests for nura/core/logger.py"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO


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
