"""
Feishu Bot for Nura - Event-driven chat agent.

This module provides the main entry point for the Feishu integration.
No path patching needed - all imports are clean Nura imports.
"""

import json
import warnings
import uuid
from typing import Any

import lark_oapi as lark
from nura.core.logger import logger

# Nura imports - clean and simple
from nura.event import Event, EventType
from nura.services.base import ClientFactory
from nura.integrations.base import BaseBot
from nura.integrations.feishu.client import FeishuClient
from nura.config import get_config, ConfigManager
from nura.config.loader import load_json  # For backward compatibility
from nura.utils import load_json_config
from nura.utils.image_processor import ImageProcessor

# Suppress pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


# Global components (for backward compatibility with event handler)
lane_queue = None


# Event handler for WebSocket
def do_p2_im_message_receive_v1(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
    """Callback for P2P messages - routes to Event Queue"""
    try:
        event_dict = json.loads(lark.JSON.marshal(data))
        logger.info(f"Received P2P Message Event: {event_dict}")
        event_data = event_dict.get("event", {})
        message_data = event_data.get("message", {})
        sender_data = event_data.get("sender", {})

        msg_content = message_data.get("content", "")
        message_type = message_data.get("message_type", "text")

        text_content = ""
        base64_image = None

        if message_type == "image":
            # Handle image message
            content_json = json.loads(msg_content)
            image_key = content_json.get("image_key", "")
            if not image_key:
                logger.warning("Image message without image_key, skipping")
                return

            # Get message_id from event data
            message_id = message_data.get("message_id", "")
            logger.info(
                f"Processing image message: {image_key}, message_id: {message_id}"
            )

            # Download and process image - run in thread to avoid event loop issues
            def download_and_process_image():
                client = ClientFactory.get_client("feishu")
                # Use sync wrapper for download (requires message_id for user-sent images)
                image_bytes = client.download_image_sync(image_key, message_id)
                if not image_bytes:
                    raise Exception(f"Failed to download image: {image_key}")
                # Use sync version for image processing
                result = ImageProcessor.process_sync(image_bytes)
                if not result:
                    raise Exception(f"Failed to process image: {image_key}")
                return result

            base64_image = download_and_process_image()
            text_content = "看完图片，有什么想跟我聊的吗"
            logger.info(f"Processed image: {len(base64_image)} base64 chars")
        else:
            # Handle text message
            try:
                content_json = json.loads(msg_content)
                text_content = content_json.get("text", "")
            except Exception:
                text_content = msg_content

        chat_id = message_data.get("chat_id", "")
        user_id = sender_data.get("sender_id", {}).get("user_id", "")

        if not text_content.strip() and not base64_image:
            logger.warning("Empty message, skipping")
            return

        # Set current chat context
        ClientFactory.get_client("feishu").set_chat_id(chat_id)

        # Create event and put into queue
        event_data_dict = {"text": text_content, "user_id": user_id}
        if base64_image:
            event_data_dict["base64_image"] = base64_image

        event = Event(
            id=str(uuid.uuid4()),
            type=EventType.MAIN,
            data=event_data_dict,
            conversation_id=chat_id,
        )

        # Thread-safe put
        lane_queue.put_thread_safe(event)

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)


def do_message_event(data: lark.CustomizedEvent) -> None:
    """Callback for generic/customized events"""
    logger.info(f"Received Customized Event: {lark.JSON.marshal(data, indent=4)}")


# Build event dispatcher handler
_event_handler = (
    lark.EventDispatcherHandler.builder("", "")
    .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1)
    .register_p1_customized_event("im.message.receive_v1", do_message_event)
    .build()
)


class FeishuBot(BaseBot):
    """Feishu bot implementation.

    This class provides the Feishu-specific implementation of BaseBot,
    including:
    - Feishu client initialization
    - Feishu event handler
    - Feishu WebSocket client startup
    """

    def __init__(self):
        super().__init__()
        self._app_id: str = ""
        self._app_secret: str = ""

    async def initialize(self, config: dict) -> None:
        """Initialize Feishu client and common setup.

        Args:
            config: Configuration dictionary with:
                - feishu_app_id: Feishu app ID
                - feishu_app_secret: Feishu app secret
                - profile_path: Path to profile YAML
                - enable_voice_reply: Enable TTS
                - tts_config: TTS configuration
                - message_collect_seconds: Seconds to wait before triggering agent response
        """
        self._config = config

        # Extract Feishu-specific credentials
        self._app_id = config.get("feishu_app_id", "")
        self._app_secret = config.get("feishu_app_secret", "")

        if not self._app_id or not self._app_secret:
            logger.error("Missing Feishu credentials in config")
            return

        # Call common setup methods
        await self.setup_messaging_client(config)
        await self.setup_tts_service(config)
        self._system_prompt = await self.build_system_prompt(config)
        self._event_queue = await self.initialize_event_queue(config)
        self._agent = await self.initialize_agent(
            config, self._event_queue, self._system_prompt
        )

        # Set global lane_queue for event handler (backward compatibility)
        global lane_queue
        lane_queue = self._event_queue

    def get_event_handler(self) -> Any:
        """Return Feishu event handler."""
        return _event_handler

    def get_platform_name(self) -> str:
        """Return platform name."""
        return "feishu"

    def start_platform_client(self) -> None:
        """Start Feishu WebSocket client in thread."""
        cli = lark.ws.Client(
            app_id=self._app_id,
            app_secret=self._app_secret,
            event_handler=self.get_event_handler(),
            log_level=lark.LogLevel.INFO,
        )
        try:
            cli.start()
        except Exception as e:
            logger.info(f"Feishu client stopped: {e}")
        except KeyboardInterrupt:
            logger.info("Feishu client interrupted")

    # ====== Override helper methods ======

    def _get_messaging_client_class(self) -> type:
        """Get the FeishuClient class."""
        return FeishuClient

    def _get_platform_credentials(self, config: dict) -> dict:
        """Get Feishu-specific credentials."""
        return {
            "app_id": config.get("feishu_app_id", ""),
            "app_secret": config.get("feishu_app_secret", ""),
        }


def load_config(config_path: str) -> dict:
    """Load configuration from JSON file.

    DEPRECATED: Use load_platform_config() instead for new code.
    This function is kept for backward compatibility.
    """
    return load_json_config(config_path)


def load_platform_config() -> dict:
    """Load Feishu platform configuration from the new config system.

    This loads configuration from:
    1. config/default.toml
    2. config/platforms/feishu.toml (if exists)
    3. Environment variables (FEISHU_*, VOLCENGINE_*)

    Returns:
        Configuration dictionary compatible with run_feishu_bot()
    """
    config = get_config(platform="feishu")

    # Convert NuraConfig to the dict format expected by run_feishu_bot
    feishu_config = {}

    if config.platforms.feishu:
        feishu = config.platforms.feishu
        feishu_config["feishu_app_id"] = feishu.app_id
        feishu_config["feishu_app_secret"] = feishu.app_secret
        feishu_config["profile_path"] = feishu.profile_path
        feishu_config["enable_voice_reply"] = feishu.enable_voice_reply
        feishu_config["message_collect_seconds"] = feishu.message_collect_seconds

        if feishu.memory_dir:
            feishu_config["memory_dir"] = feishu.memory_dir

        if feishu.tts:
            feishu_config["tts_config"] = {
                "access_token": feishu.tts.access_token,
                "app_id": feishu.tts.app_id,
                "cluster": feishu.tts.cluster,
                "voice_type": feishu.tts.voice_type,
            }

    return feishu_config


async def run_feishu_bot(config: dict):
    """Run the Feishu bot.

    Args:
        config: Configuration dictionary with:
            - feishu_app_id: Feishu app ID
            - feishu_app_secret: Feishu app secret
            - profile_path: Path to profile YAML
            - enable_voice_reply: Enable TTS
            - tts_config: TTS configuration
            - message_collect_seconds: Seconds to wait before triggering agent response
    """
    bot = FeishuBot()
    await bot.initialize(config)
    await bot.start()
