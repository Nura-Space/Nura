"""Skill queue module for Nura."""
import asyncio
from enum import Enum
from typing import Optional, Callable, Awaitable, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    pass

from nura.skill import get_skill_manager


class SkillStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SkillTask:
    """Skill task to be executed."""
    skill_name: str
    user_input: str
    session_id: str = ""
    status: SkillStatus = SkillStatus.PENDING
    result: str = ""
    blocking: bool = False


class SkillQueue:
    """Skill task queue with serial execution support."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        self._results: asyncio.Queue = asyncio.Queue()
        self._active_count: int = 0
        self._on_complete: Optional[Callable[[SkillTask], Awaitable[None]]] = None

    def set_complete_callback(self, callback: Callable[[SkillTask], Awaitable[None]]) -> None:
        """Set callback for when skill completes."""
        self._on_complete = callback

    async def put(self, task: SkillTask) -> bool:
        """Add task to queue."""
        try:
            self._queue.put_nowait(task)
            return True
        except asyncio.QueueFull:
            return False

    async def get(self) -> SkillTask:
        """Get task from queue."""
        task = await self._queue.get()
        self._active_count += 1
        return task

    async def put_result(self, task: SkillTask) -> None:
        """Put completed task result."""
        await self._results.put(task)
        self._active_count -= 1

    async def get_result(self) -> SkillTask:
        """Get task result."""
        return await self._results.get()

    def qsize(self) -> int:
        """Get queue size."""
        return self._queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def full(self) -> bool:
        """Check if queue is full."""
        return self._queue.full()

    def task_done(self) -> None:
        """Mark task as done."""
        self._queue.task_done()
        self._active_count -= 1


class SkillWorker:
    """Worker that executes skills from the queue."""

    def __init__(
        self,
        queue: Optional[SkillQueue] = None,
        max_concurrency: int = 1,
    ):
        """
        Initialize the skill worker.

        Args:
            queue: SkillQueue instance. If None, uses global queue.
            max_concurrency: Maximum number of concurrent skill executions.
        """
        self.queue = queue or get_skill_queue()
        self.max_concurrency = max_concurrency
        self._running = False
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the worker."""
        if self._running:
            return

        self._running = True
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self._worker_task = asyncio.create_task(self._run())
        from nura.core.logger import logger
        logger.info(f"SkillWorker started with max_concurrency={self.max_concurrency}")

    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        from nura.core.logger import logger
        logger.info("SkillWorker stopped")

    async def _run(self) -> None:
        """Main worker loop."""

        while self._running:
            try:
                # Wait for a task from the queue
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            # Execute task with semaphore for concurrency control
            asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: SkillTask) -> None:
        """Execute a single skill task."""
        from nura.core.logger import logger

        if not self._semaphore:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)

        async with self._semaphore:
            try:
                task.status = SkillStatus.RUNNING
                logger.info(f"Executing skill: {task.skill_name}")

                # Get skill from manager
                skill_manager = get_skill_manager()
                skill = skill_manager.get_skill(task.skill_name)

                if not skill:
                    task.status = SkillStatus.FAILED
                    task.result = f"Skill '{task.skill_name}' not found"
                    logger.error(f"Skill not found: {task.skill_name}")
                else:
                    # Run the skill using SkillRunner
                    from nura.skill.runner import SkillRunner
                    result = await SkillRunner.run_skill(skill, task.user_input)
                    task.status = SkillStatus.COMPLETED
                    task.result = result
                    logger.info(f"Skill completed: {task.skill_name}")

            except Exception as e:
                task.status = SkillStatus.FAILED
                task.result = str(e)
                logger.error(f"Skill execution failed: {task.skill_name}, error: {e}")

            finally:
                # Mark task as done
                self.queue.task_done()

                # Put result back for retrieval
                await self.queue.put_result(task)

                # Call completion callback if set
                if self.queue._on_complete:
                    try:
                        logger.info(f"Calling skill complete callback for {task.skill_name}")
                        await self.queue._on_complete(task)
                    except Exception as e:
                        logger.error(f"Complete callback error: {e}")


# Global skill worker instance
_skill_worker: Optional[SkillWorker] = None


# Global skill queue instance
_skill_queue: Optional[SkillQueue] = None


def get_skill_worker(queue: Optional[SkillQueue] = None, max_concurrency: int = 1) -> SkillWorker:
    """Get the global skill worker instance."""
    global _skill_worker
    if _skill_worker is None:
        _skill_worker = SkillWorker(queue=queue, max_concurrency=max_concurrency)
    return _skill_worker


def get_skill_queue() -> SkillQueue:
    """Get the global skill queue instance."""
    global _skill_queue
    if _skill_queue is None:
        _skill_queue = SkillQueue()
    return _skill_queue


def reset_skill_queue() -> None:
    """Reset the global skill queue. Useful for testing."""
    global _skill_queue, _skill_worker
    _skill_queue = None
    _skill_worker = None
