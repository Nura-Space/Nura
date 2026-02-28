"""Abstract TTS service interface."""

from abc import ABC, abstractmethod
from typing import Optional


class TTSService(ABC):
    """Abstract TTS service interface"""

    @abstractmethod
    async def generate_audio(self, text: str, output_path: str) -> Optional[str]:
        """Generate audio from text, returns path or None on failure"""
        pass
