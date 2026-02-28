"""Sendable content types for Feishu messages."""

from abc import ABC
from typing import Optional

from pydantic import BaseModel, Field


class Sendable(BaseModel, ABC):
    """Base class for all sendable content types.

    This abstraction decouples tools from the Feishu SDK, making it easy
    to extend support for new content types (images, videos, etc.) in the future.
    """

    class Config:
        arbitrary_types_allowed = True


class TextContent(Sendable):
    """Plain text message."""

    text: str = Field(..., description="The text content to send")
    emoji: Optional[str] = Field(default=None, description="Optional emoji to append")


class FileContent(Sendable):
    """A file to upload and send."""

    file_path: str = Field(..., description="Absolute path to the file")
    file_type: str = Field(
        ..., description="File type: opus, mp3, wav, mp4, pdf, doc, etc."
    )
    file_name: Optional[str] = Field(
        default=None, description="Display name, defaults to basename of file_path"
    )


class AudioContent(FileContent):
    """Audio content (voice message).

    Convenience subclass for audio files. Defaults to opus format.
    """

    duration: int = Field(default=None, description="Duration in milliseconds")
