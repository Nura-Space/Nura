"""Tests for nura/services/base.py"""
from unittest.mock import MagicMock

from nura.services.base import BaseClient, ClientFactory


class MockClient(BaseClient):
    """A mock client for testing."""

    def __init__(self):
        super().__init__()
        self.messages_sent = []

    async def send(self, content):
        self.messages_sent.append(content)


class TestBaseClient:
    """Unit tests for BaseClient."""

    def test_initialization(self):
        """Test BaseClient initialization."""
        client = BaseClient()
        assert client._chat_id is None

    def test_create_class_method(self):
        """Test BaseClient.create() class method."""
        client = MockClient.create()
        assert isinstance(client, MockClient)

    def test_chat_id_property_get(self):
        """Test chat_id property getter."""
        client = BaseClient()
        assert client.chat_id is None

    def test_chat_id_property_set(self):
        """Test chat_id property setter."""
        client = BaseClient()
        client.chat_id = "test_chat_123"
        assert client._chat_id == "test_chat_123"
        assert client.chat_id == "test_chat_123"

    def test_chat_id_property_set_to_none(self):
        """Test chat_id can be set to None."""
        client = BaseClient()
        client.chat_id = "test_chat_123"
        client.chat_id = None
        assert client._chat_id is None


class TestClientFactory:
    """Unit tests for ClientFactory."""

    def setup_method(self):
        """Reset ClientFactory state before each test."""
        ClientFactory._clients = {}
        ClientFactory._instances = {}
        ClientFactory._current_platform = None

    def teardown_method(self):
        """Clean up after each test."""
        ClientFactory._clients = {}
        ClientFactory._instances = {}
        ClientFactory._current_platform = None

    def test_register(self):
        """Test registering a client class."""
        ClientFactory.register("test_platform", MockClient)
        assert "test_platform" in ClientFactory._clients
        assert ClientFactory._clients["test_platform"] == MockClient

    def test_register_multiple_platforms(self):
        """Test registering multiple client classes."""
        ClientFactory.register("platform1", MockClient)
        ClientFactory.register("platform2", MagicMock)

        assert len(ClientFactory._clients) == 2
        assert ClientFactory._clients["platform1"] == MockClient
        assert ClientFactory._clients["platform2"] == MagicMock

    def test_register_overwrites_existing(self):
        """Test that registering an existing platform overwrites it."""
        ClientFactory.register("test_platform", MockClient)
        ClientFactory.register("test_platform", MagicMock)

        assert ClientFactory._clients["test_platform"] == MagicMock

    def test_get_client_not_registered(self):
        """Test get_client returns None for unregistered platform."""
        result = ClientFactory.get_client("unregistered_platform")
        assert result is None

    def test_get_client_first_time(self):
        """Test get_client creates new instance on first call."""
        ClientFactory.register("test_platform", MockClient)

        client1 = ClientFactory.get_client("test_platform")
        client2 = ClientFactory.get_client("test_platform")

        assert isinstance(client1, MockClient)
        assert client1 is client2  # Should be singleton

    def test_get_client_singleton(self):
        """Test get_client returns singleton instance."""
        ClientFactory.register("test_platform", MockClient)

        client1 = ClientFactory.get_client("test_platform")
        client2 = ClientFactory.get_client("test_platform")

        assert client1 is client2

    def test_set_current_platform(self):
        """Test set_current_platform sets the current platform."""
        ClientFactory.set_current_platform("test_platform")
        assert ClientFactory._current_platform == "test_platform"

    def test_set_current_platform_none(self):
        """Test set_current_platform can be set to None."""
        ClientFactory.set_current_platform("test_platform")
        ClientFactory.set_current_platform(None)
        assert ClientFactory._current_platform is None

    def test_get_current_client_no_platform(self):
        """Test get_current_client returns None when no platform is set."""
        ClientFactory._current_platform = None
        result = ClientFactory.get_current_client()
        assert result is None

    def test_get_current_client_platform_not_registered(self):
        """Test get_current_client returns None for unregistered platform."""
        ClientFactory.set_current_platform("unregistered")
        result = ClientFactory.get_current_client()
        assert result is None

    def test_get_current_client_success(self):
        """Test get_current_client returns client for registered platform."""
        ClientFactory.register("test_platform", MockClient)
        ClientFactory.set_current_platform("test_platform")

        client = ClientFactory.get_current_client()
        assert isinstance(client, MockClient)

    def test_get_current_client_singleton(self):
        """Test get_current_client returns singleton."""
        ClientFactory.register("test_platform", MockClient)
        ClientFactory.set_current_platform("test_platform")

        client1 = ClientFactory.get_current_client()
        client2 = ClientFactory.get_current_client()

        assert client1 is client2

    def test_get_current_platform(self):
        """Test get_current_platform returns current platform."""
        ClientFactory.set_current_platform("test_platform")
        assert ClientFactory.get_current_platform() == "test_platform"

    def test_get_current_platform_none(self):
        """Test get_current_platform returns None when no platform is set."""
        ClientFactory._current_platform = None
        assert ClientFactory.get_current_platform() is None
