"""Global FeishuClient singleton for sending messages and files."""
import asyncio
import json
import os
from typing import Optional

import builtins
import lark_oapi as lark
from loguru import logger

from nura.services.base import BaseClient
from nura.services.messaging import MessagingService
from nura.services.sendable import Sendable, TextContent, FileContent, AudioContent
from nura.services import TTSService


class FeishuClient(BaseClient, MessagingService):
    """Global singleton wrapping lark.Client for sending messages to Feishu.

    This class encapsulates all Feishu API interactions, including:
    - Text message sending via Sendable objects
    - Voice reply via TTS (handled in send_message tool)
    - File upload and sending (audio, video, documents)

    Usage:
        # Initialize once in consumer process
        feishu_client.initialize(app_id, app_secret, config)

        # Before processing each message
        feishu_client.set_chat_id(chat_id)

        # Tools send via Sendable objects
        await feishu_client.send(TextContent(text="Hello world"))
        await feishu_client.send(AudioContent(file_path="/path/to/file.opus", file_type="opus", duration=60000))
        await feishu_client.send(FileContent(file_path="/path/to/file.pdf", file_type="pdf"))
    """

    _instance: Optional["FeishuClient"] = None

    def __init__(self):
        super().__init__()
        self._client: Optional[lark.Client] = None
        self._tts_service: Optional[TTSService] = None
        self._enable_voice: bool = False
        self._emoji_path: Optional[str] = None
        self._emoji_func: dict = {}

    @classmethod
    def get_instance(cls) -> "FeishuClient":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, app_id: str, app_secret: str):
        """Initialize the lark.Client. Must be called once in the consumer process.

        Args:
            app_id: Feishu application ID
            app_secret: Feishu application secret
        """
        if not app_id or not app_secret:
            logger.error("Feishu App ID or Secret not provided")
            return

        self._client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()

        logger.info("FeishuClient initialized")

    def set_tts_service(self, tts_service: TTSService, enable_voice: bool = True):
        """Set TTS service for voice replies."""
        self._tts_service = tts_service
        self._enable_voice = enable_voice

    def set_emoji_functions(self, emoji_func: dict):
        """Set emoji functions dictionary."""
        self._emoji_func = emoji_func

    def set_chat_id(self, chat_id: str):
        """Set the current conversation's chat_id.

        Called by consumer before agent.run() for each message.
        Since the consumer processes messages sequentially, there's no concurrency issue.
        """
        self._chat_id = chat_id

    @property
    def chat_id(self) -> Optional[str]:
        return self._chat_id

    @chat_id.setter
    def chat_id(self, value: str):
        self._chat_id = value

    @property
    def emoji_func(self) -> dict:
        """Emoji functions dictionary for SendMessage tool."""
        return self._emoji_func

    # Implementation of MessagingService abstract methods

    async def send_text(self, conversation_id: str, text: str) -> None:
        """Send text message (MessagingService interface).

        Args:
            conversation_id: The chat_id to send to
            text: The text content to send
        """
        # Use conversation_id if provided, otherwise fall back to _chat_id
        target_id = conversation_id or self._chat_id
        if not target_id:
            logger.error("conversation_id not set")
            return

        content_json = json.dumps({"text": text})

        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(lark.im.v1.CreateMessageRequestBody.builder()
                .receive_id(target_id)
                .msg_type("text")
                .content(content_json)
                .build()) \
            .build()

        try:
            response = await asyncio.to_thread(self._client.im.v1.message.create, request)
            if not response.success():
                logger.error(f"Failed to send message: {response.code} - {response.msg}")
        except Exception as e:
            logger.error(f"Exception sending message: {e}")

    async def send_file(self, conversation_id: str, file_path: str, file_type: str) -> None:
        """Send file (MessagingService interface).

        Args:
            conversation_id: The chat_id to send to
            file_path: Path to the file
            file_type: Feishu file type (opus, mp3, wav, mp4, pdf, etc.)
        """
        # Use conversation_id if provided, otherwise fall back to _chat_id
        target_id = conversation_id or self._chat_id
        if not target_id:
            logger.error("conversation_id not set")
            return

        file_content = FileContent(file_path=file_path, file_type=file_type)
        await self._send_file_to_id(target_id, file_content)

    async def send_audio(self, conversation_id: str, file_path: str, duration: int) -> None:
        """Send audio message (MessagingService interface).

        Args:
            conversation_id: The chat_id to send to
            file_path: Path to the audio file
            duration: Duration in milliseconds
        """
        # Use conversation_id if provided, otherwise fall back to _chat_id
        target_id = conversation_id or self._chat_id
        if not target_id:
            logger.error("conversation_id not set")
            return

        audio = AudioContent(file_path=file_path, file_type="opus", duration=duration)
        await self._send_audio_to_id(target_id, audio)

    async def send(self, sendable: Sendable):
        """Dispatch a Sendable to the appropriate send method.

        Args:
            sendable: A Sendable instance (TextContent, FileContent, AudioContent, etc.)
        """
        if not self._client:
            logger.error("FeishuClient not initialized")
            return
        if not self._chat_id:
            logger.error("chat_id not set")
            return

        if isinstance(sendable, TextContent):
            await self._send_text(sendable)
        elif isinstance(sendable, AudioContent):
            await self._send_audio(sendable)
        elif isinstance(sendable, FileContent):
            await self._send_file(sendable)
        else:
            logger.error(f"Unknown sendable type: {type(sendable)}")

    async def _send_text(self, text_content: TextContent):
        """Send text content."""
        if not text_content.text:
            return

        content_json = json.dumps({"text": text_content.text})

        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(lark.im.v1.CreateMessageRequestBody.builder()
                .receive_id(self._chat_id)
                .msg_type("text")
                .content(content_json)
                .build()) \
            .build()

        try:
            response = await asyncio.to_thread(self._client.im.v1.message.create, request)
            if not response.success():
                logger.error(f"Failed to send message: {response.code} - {response.msg}")
        except Exception as e:
            logger.error(f"Exception sending message: {e}")

    async def _send_audio(self, audio: AudioContent):
        """Upload and send an AudioContent."""
        if not self._chat_id:
            logger.error("chat_id not set")
            return
        await self._send_audio_to_id(self._chat_id, audio)

    async def _send_audio_to_id(self, target_id: str, audio: AudioContent):
        """Upload and send an AudioContent to a specific target_id."""
        file_key = await self._upload_file(audio.file_path, "opus", audio.duration)
        if not file_key:
            logger.error(f"Failed to upload audio: {audio.file_path}")
            return

        content_json = json.dumps({"file_key": file_key})
        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(lark.im.v1.CreateMessageRequestBody.builder()
                .receive_id(target_id)
                .msg_type("audio")
                .content(content_json)
                .build()) \
            .build()

        response = await asyncio.to_thread(self._client.im.v1.message.create, request)
        if not response.success():
            logger.error(f"Failed to send audio: {response.code} - {response.msg}")

    async def _send_file(self, file_content: FileContent):
        """Upload and send a generic file (non-audio)."""
        if not self._chat_id:
            logger.error("chat_id not set")
            return
        await self._send_file_to_id(self._chat_id, file_content)

    async def _send_file_to_id(self, target_id: str, file_content: FileContent):
        """Upload and send a generic file (non-audio) to a specific target_id."""
        file_name = os.path.basename(file_content.file_path)

        file_key = await self._upload_file(
            file_content.file_path,
            file_content.file_type,
            None  # No duration for non-audio files
        )
        if not file_key:
            logger.error(f"Failed to upload file: {file_name}")
            return

        # Determine msg_type based on file_type
        msg_type = "file"
        if file_content.file_type in ("mp4",):
            msg_type = "media"

        content_json = json.dumps({"file_key": file_key})
        request = lark.im.v1.CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(lark.im.v1.CreateMessageRequestBody.builder()
                .receive_id(target_id)
                .msg_type(msg_type)
                .content(content_json)
                .build()) \
            .build()
        response = await asyncio.to_thread(self._client.im.v1.message.create, request)
        if not response.success():
            logger.error(f"Failed to send file message: {response.code} - {response.msg}")

    async def _upload_file(self, file_path: str, file_type: str, duration: int = None) -> Optional[str]:
        """Upload a file to Feishu and return the file_key.

        Args:
            file_path: Path to the file to upload
            file_type: Feishu file type (opus, mp3, wav, mp4, pdf, etc.)
            duration: Duration in milliseconds (required for audio/video)

        Returns:
            file_key if successful, None otherwise
        """
        try:
            file = builtins.open(file_path, "rb")

            builder = lark.im.v1.CreateFileRequestBody.builder() \
                .file_type(file_type) \
                .file_name(os.path.basename(file_path)) \
                .file(file)

            if duration is not None:
                builder = builder.duration(duration)

            request = lark.im.v1.CreateFileRequest.builder() \
                .request_body(builder.build()) \
                .build()

            response = await asyncio.to_thread(self._client.im.v1.file.create, request)
            if response.success():
                return response.data.file_key
            else:
                logger.error(f"File upload failed: {response.code} - {response.msg}")
                return None
        except Exception as e:
            logger.error(f"File upload exception: {e}")
            return None

    def download_image_sync(self, image_key: str, message_id: str = None) -> bytes:
        """Download image from message using message_resource API.

        Args:
            image_key: The image key from Feishu message event
            message_id: The message ID (optional, for message resource API)

        Returns:
            Image bytes
        """
        if not self._client:
            logger.error("FeishuClient not initialized")
            return b""

        try:
            import concurrent.futures

            def _download():
                logger.info(f"Downloading image with key: {image_key}, message_id: {message_id}")

                # Use message_resource API to download user-sent images
                request = lark.im.v1.GetMessageResourceRequest.builder() \
                    .message_id(message_id or "") \
                    .file_key(image_key) \
                    .type("image") \
                    .build()

                response = self._client.im.v1.message_resource.get(request)
                logger.info(f"Image download response: success={response.success()}, code={response.code if hasattr(response, 'code') else 'N/A'}")
                return response

            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = executor.submit(_download).result()

            if not response.success():
                logger.error(f"Failed to download image: {response.code} - {response.msg}")
                return b""
            logger.info(f"Image downloaded successfully, file_name: {response.file_name if hasattr(response, 'file_name') else 'unknown'}")
            return response.file.read()
        except Exception as e:
            logger.error(f"Exception downloading image: {e}")
            return b""


# Module-level singleton accessor
# Register this client class to factory (for backward compatibility)
from nura.services.base import ClientFactory
ClientFactory.register("feishu", FeishuClient)

# Module-level client instance (backward compatibility)
# Prefer using ClientFactory.get_client("feishu") in new code
feishu_client = ClientFactory.get_client("feishu")
