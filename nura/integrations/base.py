"""
Abstract base bot for messaging platforms.

This module provides the BaseBot abstract class that contains common logic
for all messaging platform integrations (Feishu, Discord, Telegram, etc.).
"""

import asyncio
import signal
import threading
from abc import ABC, abstractmethod
from typing import Optional, Any

from nura.core.logger import logger, context_log

from nura.event import EventQueue
from nura.agent.event_driven import EventDrivenAgent, ContextConfig
from nura.services.base import ClientFactory
from nura.utils import load_json_config


class BaseBot(ABC):
    """Abstract base bot for messaging platforms.

    Provides common methods for:
    - Configuration loading
    - Messaging client setup
    - TTS service setup
    - System prompt building
    - Event queue initialization
    - Agent initialization
    - Graceful shutdown handling

    Subclasses must implement platform-specific methods:
    - initialize()
    - get_event_handler()
    - get_platform_name()
    - start_platform_client()
    """

    def __init__(self):
        self._config: dict = {}
        self._client: Optional[Any] = None
        self._event_queue: Optional[EventQueue] = None
        self._agent: Optional[EventDrivenAgent] = None
        self._system_prompt: str = ""
        self._shutdown_event: Optional[asyncio.Event] = None

    @abstractmethod
    async def initialize(self, config: dict) -> None:
        """Initialize platform-specific client and common setup.

        This method should:
        1. Call common setup methods (setup_messaging_client, setup_tts_service, etc.)
        2. Perform platform-specific initialization

        Args:
            config: Configuration dictionary
        """
        pass

    @abstractmethod
    def get_event_handler(self) -> Any:
        """Return platform-specific event handler.

        Returns:
            Platform-specific event handler (e.g., lark.EventDispatcherHandler)
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform name.

        Returns:
            Platform name (e.g., "feishu", "discord", "telegram")
        """
        pass

    @abstractmethod
    def start_platform_client(self) -> None:
        """Start the platform-specific client (e.g., WebSocket client).

        This method runs in a separate thread and should block until
        the client is stopped.
        """
        pass

    # ====== Common Methods ======

    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Configuration dictionary
        """
        return load_json_config(config_path)

    async def setup_messaging_client(self, config: dict) -> None:
        """Setup messaging client by registering platform client to ClientFactory.

        Args:
            config: Configuration dictionary containing platform credentials
        """
        platform_name = self.get_platform_name()

        # Import platform-specific client class (subclasses should override or configure)
        client_class = self._get_messaging_client_class()
        if client_class:
            ClientFactory.register(platform_name, client_class)
            ClientFactory.set_current_platform(platform_name)

            # Initialize client with credentials from config
            credentials = self._get_platform_credentials(config)
            if credentials:
                client = ClientFactory.get_client(platform_name)
                if hasattr(client, "initialize"):
                    client.initialize(**credentials)

                # Setup emoji functions if available
                if hasattr(client, "set_emoji_functions"):
                    from nura.integrations.feishu.emoji import load_emoji_functions

                    emoji_functions = load_emoji_functions()
                    client.set_emoji_functions(emoji_functions)

                logger.info(
                    f"{platform_name.capitalize()} messaging client initialized"
                )

    async def setup_tts_service(self, config: dict) -> None:
        """Setup TTS service if enabled in configuration.

        Args:
            config: Configuration dictionary
        """
        enable_voice = config.get("enable_voice_reply", False)
        if not enable_voice:
            return

        tts_config = config.get("tts_config", {})
        platform_name = self.get_platform_name()

        try:
            from nura.services.tts_service import VolcengineTTS

            tts_service = VolcengineTTS({"tts_config": tts_config})

            client = ClientFactory.get_client(platform_name)
            if hasattr(client, "set_tts_service"):
                client.set_tts_service(tts_service, enable_voice)
                logger.info(f"TTS service enabled for {platform_name}")
        except Exception as e:
            logger.error(f"Failed to setup TTS service: {e}")

    async def build_system_prompt(self, config: dict) -> str:
        """Build system prompt from profile and skills.

        Args:
            config: Configuration dictionary

        Returns:
            System prompt string
        """
        import os

        system_prompt = ""

        profile_path = config.get("profile_path", "")
        if profile_path and os.path.exists(profile_path):
            from nura.prompts import build_roleplay_prompt

            system_prompt = build_roleplay_prompt(profile_path)
            logger.info(f"Loaded system prompt from {profile_path}")

        # Build skills summary and append to system prompt
        from nura.skill import get_skill_manager

        skills_manager = get_skill_manager()
        skills_manager.load_skills()
        skills_summary = skills_manager.build_skills_summary(lang="zh")
        if skills_summary:
            if system_prompt:
                system_prompt += "\n\n"
            system_prompt += f"## Available Skills\n{skills_summary}"
            logger.info(
                f"Loaded {len(skills_manager.list_skills(filter_unavailable=False))} skills"
            )

        context_log(system_prompt)
        return system_prompt

    async def initialize_event_queue(self, config: dict) -> EventQueue:
        """Initialize event queue.

        Args:
            config: Configuration dictionary

        Returns:
            Initialized EventQueue instance
        """
        event_queue = EventQueue(debounce_seconds=0.5)
        logger.info("Event queue initialized")
        return event_queue

    async def initialize_agent(
        self, config: dict, event_queue: EventQueue, system_prompt: str
    ) -> EventDrivenAgent:
        """Initialize the event-driven agent.

        Args:
            config: Configuration dictionary
            event_queue: EventQueue instance
            system_prompt: System prompt string

        Returns:
            Initialized EventDrivenAgent instance
        """
        message_collect_seconds = config.get("message_collect_seconds", 10.0)

        context_config = ContextConfig(
            max_tokens=128000,
            compress_threshold=0.5,
            keep_turns=10,
            compress_cooldown=60,
        )

        agent = EventDrivenAgent(
            lane_queue=event_queue,
            system_prompt=system_prompt,
            message_collect_seconds=message_collect_seconds,
            debounce_seconds=0.5,
            context_config=context_config,
        )

        logger.info("Agent initialized successfully")
        return agent

    async def start(self) -> None:
        """Start the bot (start agent and platform client).

        This method:
        1. Starts the agent in background
        2. Sets up signal handlers for graceful shutdown
        3. Starts the platform client in a separate thread
        4. Waits for shutdown signal
        """
        # Start the agent in background
        asyncio.create_task(self._agent.start())
        logger.info(f"{self.get_platform_name().capitalize()} agent started")

        # Setup signal handlers
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()

        # Start platform client in a separate thread
        platform_thread = threading.Thread(
            target=self.start_platform_client, daemon=True
        )
        platform_thread.start()

        logger.info(f"✅ {self.get_platform_name().capitalize()} bot is running!")

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Gracefully stop the agent
        await self.stop()

    async def stop(self) -> None:
        """Gracefully stop the bot."""
        logger.info("Stopping bot...")
        if self._agent:
            try:
                await self._agent.stop()
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")

        logger.info("Shutdown complete")
        import sys

        sys.exit(0)

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(sig, frame):
            logger.info("Shutting down gracefully...")
            if self._shutdown_event:
                self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    # ====== Helper Methods (override in subclasses) ======

    def _get_messaging_client_class(self) -> Optional[type]:
        """Get the messaging client class for this platform.

        Override in subclasses to return platform-specific client class.

        Returns:
            Client class or None
        """
        # Default implementation returns None - subclasses should override
        return None

    def _get_platform_credentials(self, config: dict) -> Optional[dict]:
        """Get platform-specific credentials from config.

        Override in subclasses to provide platform-specific credentials.

        Args:
            config: Configuration dictionary

        Returns:
            Credentials dictionary or None
        """
        # Default implementation - subclasses should override
        return None
