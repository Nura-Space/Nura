"""Abstract messaging service interface."""

from abc import ABC, abstractmethod


class MessagingService(ABC):
    """Abstract messaging service interface"""

    @abstractmethod
    async def send_text(self, conversation_id: str, text: str) -> None:
        """Send text message"""
        pass

    @abstractmethod
    async def send_file(
        self, conversation_id: str, file_path: str, file_type: str
    ) -> None:
        """Send file"""
        pass

    @abstractmethod
    async def send_audio(
        self, conversation_id: str, file_path: str, duration: int
    ) -> None:
        """Send audio message"""
        pass
