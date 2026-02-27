"""Abstract base client interface for messaging platforms."""
from abc import ABC
from typing import Optional, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class BaseClient(ABC):
    """Abstract base client for messaging platforms.

    Provides common attributes like chat_id that all platform clients share.
    """

    def __init__(self):
        self._chat_id: Optional[str] = None

    @classmethod
    def create(cls) -> "BaseClient":
        """Create a new instance of this client."""
        return cls()

    @property
    def chat_id(self) -> Optional[str]:
        """Get the current chat/conversation ID."""
        return self._chat_id

    @chat_id.setter
    def chat_id(self, value: str):
        """Set the current chat/conversation ID."""
        self._chat_id = value


class ClientFactory:
    """Factory for creating and managing platform clients.

    Usage:
        # Register a client for a platform
        ClientFactory.register("feishu", FeishuClient)

        # Get the client (singleton per platform)
        client = ClientFactory.get_client("feishu")
    """

    _clients: Dict[str, Type["BaseClient"]] = {}
    _instances: Dict[str, "BaseClient"] = {}
    _current_platform: Optional[str] = None

    @classmethod
    def register(cls, platform: str, client_class: Type["BaseClient"]) -> None:
        """Register a client class for a platform."""
        cls._clients[platform] = client_class

    @classmethod
    def get_client(cls, platform: str) -> Optional["BaseClient"]:
        """Get or create a client instance for a platform (singleton)."""
        if platform not in cls._instances:
            client_class = cls._clients.get(platform)
            if client_class:
                cls._instances[platform] = client_class.create()
        return cls._instances.get(platform)

    @classmethod
    def set_current_platform(cls, platform: str) -> None:
        """Set the current active platform."""
        cls._current_platform = platform

    @classmethod
    def get_current_client(cls) -> Optional["BaseClient"]:
        """Get the current active client."""
        if cls._current_platform:
            return cls.get_client(cls._current_platform)
        return None

    @classmethod
    def get_current_platform(cls) -> Optional[str]:
        """Get the current active platform name."""
        return cls._current_platform
