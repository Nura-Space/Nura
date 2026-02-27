"""
Event-driven TalkAgent with Lane Queue integration.

Architecture:
- Outer loop: await lane.get() with debounce for batch message collection
- Inner loop: ReAct循环 with token limit compression
- Context Manager: Turn-based compression for memory management

Features:
- Persistent agent process (ever-running)
- Event-driven processing via Lane Queue
- Token limit handling with context compression (turn-based)
- Built-in error recovery with retry + exponential backoff
"""

import asyncio
import time
from typing import List, Optional

from loguru import logger

from nura.context import ContextConfig, ContextManager


class EventDrivenAgent:
    """
    Event-driven TalkAgent with Lane Queue integration.

    Architecture:
    - Outer loop: await lane.get() with debounce for batch message collection
    - Inner loop: ReAct循环 with token limit compression
    - Context Manager: Turn-based compression for memory management

    Features:
    - Persistent agent process (ever-running)
    - Event-driven processing via Lane Queue
    - Token limit handling with context compression (turn-based)
    - Built-in error recovery with retry + exponential backoff
    """

    def __init__(
        self,
        lane_queue,
        system_prompt: str = "",
        debounce_seconds: float = 0.5,
        message_collect_seconds: float = 10.0,
        context_config: Optional[ContextConfig] = None,
    ):
        """
        Initialize the event-driven TalkAgent.

        Args:
            lane_queue: LaneQueue instance for event processing
            system_prompt: System prompt for the agent
            debounce_seconds: Seconds to wait for batch message collection within a conversation
            message_collect_seconds: Seconds to wait before triggering agent response, allowing time for user to send multiple messages
            context_config: Context management configuration
        """
        # Import here to avoid circular dependencies
        from nura.agent.toolcall import ToolCallAgent
        from nura.tool.collection import ToolCollection
        from nura.tool import EndChat, SendMessage, SendFile, Skills
        from nura.tool.web_search import WebSearch

        # Initialize base agent
        self._base_agent = ToolCallAgent(
            system_prompt=system_prompt,
            next_step_prompt="",
            available_tools=ToolCollection(
                EndChat(),
                SendFile(),
                SendMessage(),
                Skills(),
                WebSearch()
            ),
            special_tool_names=[EndChat().name],
            max_steps=30,  # Keep as safety limit, but compression should prevent hitting it
        )

        # Configuration
        self._lane_queue = lane_queue
        self._debounce_seconds = debounce_seconds
        self._message_collect_seconds = message_collect_seconds
        self._context = ContextManager(context_config)

        # State
        self._running = False
        self._current_conversation: Optional[str] = None

        # Error recovery
        self._retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 30.0,
        }

        # Initialize SkillWorker
        from nura.core.skill_queue import get_skill_queue, get_skill_worker
        self._skill_queue = get_skill_queue()
        self._skill_worker = get_skill_worker(self._skill_queue)

        # Set up callback for skill completion
        self._skill_queue.set_complete_callback(self._on_skill_complete)
        from nura.core.logger import logger
        logger.info(f"Skill complete callback set on queue: {id(self._skill_queue)}")

    @property
    def agent(self):
        """Get the underlying base agent"""
        return self._base_agent

    @property
    def memory(self):
        """Get agent memory"""
        return self._base_agent.memory

    @property
    def context(self):
        """Get context manager"""
        return self._context

    def _sync_context_with_memory(self) -> None:
        """Sync the ContextManager with the agent's memory.

        This ensures the ContextManager has the same messages as the memory,
        so it can properly track turns and trigger compression.
        """
        # Get messages from memory that aren't in context yet
        memory_messages = self.memory.messages

        if not memory_messages:
            return

        # If context is empty, add all messages
        if not self._context._messages:
            for msg in memory_messages:
                self._context.add_message(msg)
            return

        # Otherwise, only add new messages
        existing_count = len(self._context._messages)
        new_messages = memory_messages[existing_count:]

        for msg in new_messages:
            self._context.add_message(msg)

        logger.debug(f"Synced {len(new_messages)} new messages to context manager")

    @property
    def is_running(self) -> bool:
        """Agent 是否正在处理任务 (RUNNING 状态)"""
        from nura.core.schema import AgentState
        return self._base_agent.state == AgentState.RUNNING

    @property
    def is_idle(self) -> bool:
        """Agent 是否空闲 (IDLE 状态)"""
        from nura.core.schema import AgentState
        return self._base_agent.state == AgentState.IDLE

    async def start(self) -> None:
        """Start the event-driven agent loop"""
        self._running = True

        # Start the skill worker
        await self._skill_worker.start()

        logger.info("Event-driven TalkAgent started")

        while self._running:
            try:
                # Process pending thread-safe puts first
                await self._lane_queue.process_pending_puts()

                # Outer loop: wait for events from Lane Queue
                event = await self._lane_queue.get(timeout=1.0)

                if event is None:
                    # Timeout, check if we should compress
                    self._sync_context_with_memory()
                    if self._context.needs_compression:
                        await self._compress_context()
                    continue

                # Set current conversation
                self._current_conversation = event.conversation_id

                # Process the event
                await self._process_event(event)

            except asyncio.CancelledError:
                logger.info("Agent loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                await self._handle_error(e)

    async def stop(self) -> None:
        """Stop the agent"""
        self._running = False

        # Stop the skill worker
        await self._skill_worker.stop()

        await self._base_agent.cleanup()

    async def _process_event(self, event) -> None:
        """Process a single event from the lane"""
        from nura.event.types import Event, EventType

        if not isinstance(event, Event):
            logger.warning(f"Unknown event type: {type(event)}")
            return

        logger.info(f"Processing event: {event.type} - {event.data}")

        if event.type == EventType.MAIN:
            await self._handle_main_event(event)
        elif event.type == EventType.BACKGROUND:
            await self._handle_subagent_event(event)

    async def _handle_main_event(self, event) -> None:
        """Handle a main lane event (user message)"""
        # Set chat_id for current platform client
        conversation_id = event.conversation_id
        from nura.services.base import ClientFactory
        client = ClientFactory.get_current_client()
        if client:
            client.chat_id = conversation_id
        logger.info(f"Set chat_id to: {conversation_id}")

        # Wait for user to potentially send more messages before triggering agent response
        # This allows time for user to compose and send multiple messages
        logger.info(f"Waiting {self._message_collect_seconds}s for potential user messages...")
        await asyncio.sleep(self._message_collect_seconds)

        # Check if we need to collect debounced messages
        events = await self._lane_queue.get_with_debounce(
            event.conversation_id,
            self._debounce_seconds
        )

        # Extract content and base64_image from event data - support both dict and object formats
        def get_content_and_image(e):
            data = e.data
            if isinstance(data, dict):
                text = data.get("text", "") or data.get("content", "")
                base64_image = data.get("base64_image")
                return text, base64_image
            return getattr(data, "content", str(data)), None

        # If multiple events, combine their content (use first event's image if any)
        base64_image = None
        if len(events) > 1:
            combined_content = "\n".join([get_content_and_image(e)[0] for e in events])
            logger.info(f"Combined {len(events)} messages: {combined_content}...")
            user_input = combined_content
            # Get base64_image from the first event (the original user message)
            _, base64_image = get_content_and_image(events[0])
        else:
            user_input, base64_image = get_content_and_image(event)

        # Check token limit before processing
        self._sync_context_with_memory()
        if self._context.needs_compression:
            await self._compress_context()

        # Run the inner ReAct loop
        try:
            await self._run_react_loop(user_input, base64_image)
        except Exception as e:
            logger.error(f"ReAct loop error: {e}")
            await self._handle_error(e)

    async def _handle_subagent_event(self, event) -> None:
        """Handle a subagent lane event (async task result)"""
        # Get conversation_id from event
        conversation_id = event.conversation_id

        # Set chat_id for current platform client
        from nura.services.base import ClientFactory
        client = ClientFactory.get_current_client()
        if client:
            client.chat_id = conversation_id
        self._current_conversation = conversation_id

        result = event.data

        # Handle both dict (from SkillAnnounceHandler) and object formats
        if isinstance(result, dict):
            skill_name = result.get("skill_name", "unknown")
            result_content = result.get("result", "")
            user_input = f"[Skill completed] {skill_name}: {result_content}"
        elif hasattr(result, 'result'):
            # Legacy object format (e.g., SkillTask)
            user_input = f"[Task completed] {result.result}"

        # Run ReAct loop to continue processing with the skill result
        try:
            await self._run_react_loop(user_input)
        except Exception as e:
            logger.error(f"ReAct loop error after subagent event: {e}")
            await self._handle_error(e)

    async def _on_skill_complete(self, task) -> None:
        """
        Callback for when a skill completes.
        Uses LLM to summarize the skill result, then injects it as a BACKGROUND event
        to trigger the main agent to respond.
        """
        from nura.core.logger import logger
        logger.info(f">>> _on_skill_complete called for {task.skill_name}, status: {task.status}")

        # Prepare skill result for summarization
        from nura.core.schema import Message
        from nura.core.skill_queue import SkillStatus
        from nura.event.types import Event, EventType

        logger.info(f"Skill completed: {task.skill_name}, status: {task.status}")

        # Prepare skill result for summarization
        if task.status == SkillStatus.COMPLETED:
            skill_result = task.result
            system_msg = "你是技能结果总结助手。请用简洁的语言总结以下技能执行结果。"
            user_msg = f"技能名称: {task.skill_name}\n执行结果:\n{skill_result}"

            # Call LLM to summarize
            try:
                from nura.llm import LLM
                llm = LLM()
                response = await llm.ask(
                    messages=[
                        Message.system_message(system_msg),
                        Message.user_message(user_msg)
                    ]
                )
                # llm.ask() returns a string directly
                summary = response if response else skill_result
                logger.info(f"Skill result summarized: {summary}")
            except Exception as e:
                logger.error(f"Failed to summarize skill result: {e}")
                summary = skill_result

            # Inject as BACKGROUND event to trigger main agent
            event = Event(
                id=f"skill_{task.skill_name}_{int(time.time())}",
                type=EventType.BACKGROUND,
                data={
                    "skill_name": task.skill_name,
                    "result": summary,
                    "raw_result": skill_result
                },
                conversation_id=task.session_id or "default"
            )
            await self._lane_queue.put(event)
            logger.info(f"Skill result injected as BACKGROUND event: {task.skill_name}")

        elif task.status == SkillStatus.FAILED:
            # Inject failed event
            event = Event(
                id=f"skill_fail_{task.skill_name}_{int(time.time())}",
                type=EventType.BACKGROUND,
                data={
                    "skill_name": task.skill_name,
                    "result": None,
                    "error": task.result
                },
                conversation_id=task.session_id or "default"
            )
            await self._lane_queue.put(event)
            logger.info(f"Skill failed event injected: {task.skill_name}")

    async def _run_react_loop(self, user_input: str, base64_image: str = None) -> None:
        """
        Run the inner ReAct loop.

        This is the core agent loop that:
        1. Thinks (calls LLM)
        2. Acts (executes tools)
        3. Checks for skill results
        4. Handles token limits
        """
        from nura.core.schema import AgentState, Message

        # Add user message to memory
        self.memory.add_message(Message.user_message(user_input, base64_image=base64_image))

        # Set agent state to running
        async with self._base_agent.state_context(AgentState.RUNNING):
            while (
                self._base_agent.current_step < self._base_agent.max_steps
                and self._base_agent.state != AgentState.FINISHED
            ):
                self._base_agent.current_step += 1
                logger.info(f"Step {self._base_agent.current_step}/{self._base_agent.max_steps}")

                # Check for new messages from Main Lane
                self._check_for_new_messages()

                # Note: Skill results are now handled by SkillAnnounceHandler (steer/followup mode)
                # No need to check skill queue here

                # Think (LLM call)
                should_act = await self._base_agent.think()
                if not should_act:
                    continue

                # Act (execute tools)
                await self._base_agent.act()

                # Check for stuck state
                if self._base_agent.is_stuck():
                    self._base_agent.handle_stuck_state()

                # Check token limit after each step
                self._sync_context_with_memory()
                if self._context.needs_compression:
                    compress_success = await self._compress_context()
                    if not compress_success:
                        # If compression failed, check if we should continue
                        logger.warning("Context compression failed, checking if should continue")

            # Reset state if max steps reached
            if self._base_agent.current_step >= self._base_agent.max_steps:
                self._base_agent.current_step = 0
                self._base_agent.state = AgentState.IDLE

    def _check_for_new_messages(self) -> None:
        """Check the lane queue for new messages"""
        try:
            if not self._lane_queue.main_empty():
                # Check if there's a message for current conversation
                # Note: This is a non-blocking check
                event = self._lane_queue.lane_queue.get_nowait()
                if event and event.conversation_id == self._current_conversation:
                    logger.info(f"Received new message: {event.data.content}")
                    from nura.core.schema import Message
                    self.memory.add_message(Message.user_message(event.data.content))
                elif event:
                    # Put it back if different conversation
                    import asyncio
                    asyncio.create_task(self._lane_queue.lane_queue.put(event))
        except Exception as e:
            logger.debug(f"Error checking for new messages: {e}")

    async def _compress_context(self) -> bool:
        """Compress context using the context manager"""
        from nura.core.schema import Message
        logger.info("Triggering context compression")

        async def summarize(messages: List[Message]) -> str:
            # Use the LLM to summarize messages
            from nura.llm import LLM
            from nura.core.schema import Message as Msg

            # Prepare messages for summarization
            system_prompt = "你是对话摘要助手。请简洁地总结以下对话的主要内容，保留关键信息和用户意图。"
            conversation = "\n".join([
                f"{msg.role}: {msg.content or '[无内容]'}"
                for msg in messages if msg.content
            ])

            try:
                llm = LLM()
                response = await llm.ask(
                    messages=[
                        Msg.system_message(system_prompt),
                        Msg.user_message(f"请总结以下对话:\n\n{conversation}")
                    ],
                    stream=False
                )
                return response if response else f"[Summary of {len(messages)} previous messages]"
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                return f"[Summary of {len(messages)} previous messages]"

        return await self._context.compress(summarize)

    async def _handle_error(self, error: Exception) -> None:
        """Handle errors with retry and exponential backoff"""
        from nura.core.schema import AgentState

        retries = 0
        delay = self._retry_config["base_delay"]

        while retries < self._retry_config["max_retries"]:
            try:
                logger.info(f"Retrying after error (attempt {retries + 1}): {error}")
                await asyncio.sleep(delay)

                # Exponential backoff
                delay = min(delay * 2, self._retry_config["max_delay"])
                retries += 1

                # Try to continue
                self._base_agent.state = AgentState.IDLE
                return

            except Exception as e:
                logger.error(f"Retry failed: {e}")
                error = e
                continue

        # All retries failed
        logger.error(f"All retries exhausted: {error}")
        self._base_agent.state = AgentState.ERROR
