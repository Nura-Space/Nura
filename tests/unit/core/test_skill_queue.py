"""Tests for skill queue module."""
import pytest
from unittest.mock import AsyncMock

from nura.core.skill_queue import (
    SkillQueue,
    SkillWorker,
    SkillTask,
    SkillStatus,
    get_skill_queue,
    get_skill_worker,
    reset_skill_queue,
)


class TestSkillTask:
    """Test cases for SkillTask dataclass."""

    @pytest.mark.unit
    def test_create_task(self):
        """Test creating a skill task."""
        task = SkillTask(
            skill_name="test_skill",
            user_input="test input",
            session_id="session_123"
        )

        assert task.skill_name == "test_skill"
        assert task.user_input == "test input"
        assert task.session_id == "session_123"
        assert task.status == SkillStatus.PENDING
        assert task.result == ""
        assert task.blocking is False

    @pytest.mark.unit
    def test_create_task_defaults(self):
        """Test creating a skill task with defaults."""
        task = SkillTask(skill_name="test_skill", user_input="test input")

        assert task.session_id == ""
        assert task.status == SkillStatus.PENDING
        assert task.result == ""
        assert task.blocking is False


class TestSkillQueue:
    """Test cases for SkillQueue."""

    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset global queue before each test."""
        reset_skill_queue()
        yield
        reset_skill_queue()

    @pytest.mark.unit
    def test_create_queue(self):
        """Test creating a skill queue."""
        queue = SkillQueue()

        assert queue.qsize() == 0
        assert queue.empty() is True
        assert queue.full() is False
        assert queue._active_count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_put_task(self):
        """Test putting a task in the queue."""
        queue = SkillQueue()
        task = SkillTask(skill_name="test", user_input="input")

        result = await queue.put(task)

        assert result is True
        assert queue.qsize() == 1
        assert queue.empty() is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_task(self):
        """Test getting a task from the queue."""
        queue = SkillQueue()
        task = SkillTask(skill_name="test", user_input="input")
        await queue.put(task)

        retrieved_task = await queue.get()

        assert retrieved_task.skill_name == "test"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_result(self):
        """Test getting a result."""
        queue = SkillQueue()
        task = SkillTask(skill_name="test", user_input="input", result="done")
        await queue.put_result(task)

        result_task = await queue.get_result()

        assert result_task.result == "done"

    @pytest.mark.unit
    def test_set_complete_callback(self):
        """Test setting completion callback."""
        queue = SkillQueue()
        callback = AsyncMock()

        queue.set_complete_callback(callback)

        assert queue._on_complete is callback


class TestSkillWorker:
    """Test cases for SkillWorker."""

    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset global queue before each test."""
        reset_skill_queue()
        yield
        reset_skill_queue()

    @pytest.mark.unit
    def test_create_worker(self):
        """Test creating a skill worker."""
        worker = SkillWorker(max_concurrency=3)

        assert worker.max_concurrency == 3
        assert worker._running is False

    @pytest.mark.unit
    def test_create_worker_with_queue(self):
        """Test creating a worker with a custom queue."""
        queue = SkillQueue()
        worker = SkillWorker(queue=queue, max_concurrency=2)

        assert worker.queue is queue
        assert worker.max_concurrency == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_worker(self):
        """Test starting the worker."""
        worker = SkillWorker(max_concurrency=1)

        await worker.start()

        assert worker._running is True
        assert worker._semaphore is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_worker_already_running(self):
        """Test starting an already running worker."""
        worker = SkillWorker(max_concurrency=1)
        worker._running = True

        await worker.start()

        # Should not create new semaphore
        assert worker._semaphore is None


class TestSkillQueueFunctions:
    """Test module-level functions."""

    @pytest.fixture(autouse=True)
    def reset_queue(self):
        """Reset global queue before each test."""
        reset_skill_queue()
        yield
        reset_skill_queue()

    @pytest.mark.unit
    def test_get_skill_queue(self):
        """Test getting global skill queue."""
        queue1 = get_skill_queue()
        queue2 = get_skill_queue()

        # Should return the same instance
        assert queue1 is queue2

    @pytest.mark.unit
    def test_get_skill_worker(self):
        """Test getting global skill worker."""
        worker1 = get_skill_worker(max_concurrency=2)
        worker2 = get_skill_worker(max_concurrency=3)

        # First call creates, second returns same
        assert worker1 is worker2

    @pytest.mark.unit
    def test_reset_skill_queue(self):
        """Test resetting global queue."""
        queue1 = get_skill_queue()
        reset_skill_queue()
        queue2 = get_skill_queue()

        # Should be a new instance
        assert queue1 is not queue2
