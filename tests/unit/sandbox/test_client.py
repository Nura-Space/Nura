"""Tests for sandbox client module."""
import pytest

from nura.sandbox.client import LocalSandboxClient


class TestLocalSandboxClient:
    """Test cases for LocalSandboxClient."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test client initialization."""
        client = LocalSandboxClient()

        assert client is not None

    @pytest.mark.unit
    def test_inherits_from_abc(self):
        """Test that LocalSandboxClient inherits from BaseSandboxClient."""
        from nura.sandbox.client import BaseSandboxClient
        assert issubclass(LocalSandboxClient, BaseSandboxClient)
