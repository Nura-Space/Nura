"""
Event Queue System for Nura

Generalized dual-priority queue with Main + Background lanes:
- Main: User messages (high priority)
- Background: Async tasks (lower priority)
"""

import asyncio
from typing import Optional
import time
import threading
from nura.event.types import Event, EventType


class EventQueue:
    """
    Async Event Queue System with debounce support.

    Features:
    - Two lanes: Main (user messages) and Background (async tasks)
    - Thread-safe asyncio Queue implementation
    - Thread-safe put operations for cross-thread communication
    - Debounce support for batch message processing
    - Priority-based retrieval (Main > Background)
    """

    def __init__(self, debounce_seconds: float = 0.5):
        self._main_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._background_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._debounce_seconds = debounce_seconds

        # Thread-safe pending puts
        self._pending_puts: list[tuple[asyncio.Queue, Event]] = []
        self._puts_lock = threading.Lock()

    def put_thread_safe(self, event: Event) -> None:
        """
        Thread-safe put from any thread.

        This method can be called from any thread (e.g., WebSocket callback thread).
        The actual put will be done by the main event loop.

        Args:
            event: The event to enqueue
        """
        if event.type == EventType.MAIN:
            queue = self._main_queue
        else:
            queue = self._background_queue

        with self._puts_lock:
            self._pending_puts.append((queue, event))

    async def process_pending_puts(self) -> int:
        """
        Process pending thread-safe puts.

        Call this regularly from the main event loop.

        Returns:
            Number of events processed
        """
        count = 0
        with self._puts_lock:
            pending = self._pending_puts
            self._pending_puts = []

        for queue, event in pending:
            await queue.put(event)
            count += 1

        return count

    async def put(self, event: Event) -> None:
        """
        Put an event into the appropriate queue.

        Args:
            event: The event to enqueue
        """
        if event.type == EventType.MAIN:
            await self._main_queue.put(event)
        else:
            await self._background_queue.put(event)

    async def get(self, timeout: Optional[float] = None) -> Optional[Event]:
        """
        Get the next event from any queue.

        Main queue has priority over background queue.
        Returns None if timeout is reached.

        Args:
            timeout: Maximum time to wait for an event

        Returns:
            The next Event, or None if timeout
        """
        start_time = time.time()
        remaining = timeout

        while True:
            # Check main queue first (priority)
            try:
                event = self._main_queue.get_nowait()
                return event
            except asyncio.QueueEmpty:
                pass

            # Check background queue if main is empty
            try:
                event = self._background_queue.get_nowait()
                return event
            except asyncio.QueueEmpty:
                pass

            # Wait for new events if timeout not reached
            if timeout is not None:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    return None

            # Wait for any queue to have data
            wait_time = min(remaining, 0.1) if remaining else 0.1
            try:
                # Use wait_for on both queues
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(self._wait_main()),
                        asyncio.create_task(self._wait_background()),
                    ],
                    timeout=wait_time,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                # Cancel pending tasks
                for task in pending:
                    task.cancel()

                # Return the result from the completed task
                if done:
                    # Get the first completed task's result
                    completed_task = done.pop()
                    return completed_task.result()
            except asyncio.CancelledError:
                return None

    async def _wait_main(self) -> Event:
        """Wait for main queue to have an event"""
        return await self._main_queue.get()

    async def _wait_background(self) -> Event:
        """Wait for background queue to have an event"""
        return await self._background_queue.get()

    async def get_with_debounce(
        self,
        conversation_id: str,
        debounce_seconds: Optional[float] = None,
    ) -> list[Event]:
        """
        Get events for a conversation with debounce.

        Collects all pending events for the conversation and returns them
        as a batch after waiting for debounce_seconds of silence.

        Args:
            conversation_id: The conversation to collect events for
            debounce_seconds: How long to wait for more events

        Returns:
            List of Events collected during the debounce window
        """
        debounce = debounce_seconds or self._debounce_seconds
        events: list[Event] = []

        while True:
            # Try to get next event
            event = await self.get(timeout=debounce)

            if event is None:
                # Timeout reached, return collected events
                return events

            # Check if event belongs to the same conversation
            if event.conversation_id == conversation_id:
                events.append(event)
                # Reset debounce timer for each new event
                debounce = debounce_seconds or self._debounce_seconds
            else:
                # Different conversation, put it back and return
                await self.put(event)
                return events

    def empty(self) -> bool:
        """Check if both queues are empty"""
        return self._main_queue.empty() and self._background_queue.empty()

    def main_empty(self) -> bool:
        """Check if main queue is empty"""
        return self._main_queue.empty()

    @property
    def lane_queue(self):
        """Access the main queue directly for low-level operations"""
        return self._main_queue

    def qsize(self) -> dict[EventType, int]:
        """Get queue sizes for each type"""
        return {
            EventType.MAIN: self._main_queue.qsize(),
            EventType.BACKGROUND: self._background_queue.qsize(),
        }
