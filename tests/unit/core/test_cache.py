"""Tests for nura/core/cache.py"""
import time

from nura.core.cache import CacheManager, SessionData


class TestCacheManager:
    """Unit tests for CacheManager."""

    def setup_method(self):
        """Reset the singleton before each test."""
        # Reset the singleton
        CacheManager._instance = None
        CacheManager._sessions = {}
        self.cache = CacheManager()

    def teardown_method(self):
        """Clean up after each test."""
        CacheManager._instance = None
        CacheManager._sessions = {}

    def test_get_session_empty_session_id(self):
        """Test that get_session returns None for empty session_id."""
        result = self.cache.get_session("")
        assert result is None

    def test_get_session_none_session_id(self):
        """Test that get_session returns None for None session_id."""
        result = self.cache.get_session(None)
        assert result is None

    def test_get_session_not_exists(self):
        """Test that get_session returns None for non-existent session."""
        result = self.cache.get_session("non_existent_session")
        assert result is None

    def test_get_session_expired(self):
        """Test that get_session returns None for expired session."""
        # Create a session that expired 20 seconds ago
        session_id = "expired_session"
        self.cache._sessions[session_id] = SessionData(
            response_id="resp_123",
            expire_at=time.time() - 20,  # Expired 20 seconds ago
            last_message_count=5
        )
        result = self.cache.get_session(session_id)
        assert result is None

    def test_get_session_within_buffer(self):
        """Test that get_session returns None when within expiration buffer."""
        session_id = "buffer_session"
        # Set expire_at to 5 seconds from now (within the 10 second buffer)
        self.cache._sessions[session_id] = SessionData(
            response_id="resp_123",
            expire_at=time.time() + 5,
            last_message_count=5
        )
        result = self.cache.get_session(session_id)
        assert result is None

    def test_get_session_valid(self):
        """Test that get_session returns session data for valid session."""
        session_id = "valid_session"
        expire_at = time.time() + 3600  # 1 hour from now
        self.cache._sessions[session_id] = SessionData(
            response_id="resp_123",
            expire_at=expire_at,
            last_message_count=5
        )
        result = self.cache.get_session(session_id)
        assert result is not None
        assert result.response_id == "resp_123"
        assert result.last_message_count == 5

    def test_update_session_empty_session_id(self):
        """Test that update_session does nothing for empty session_id."""
        self.cache.update_session("", "resp_123", 5, 1000)
        assert len(self.cache._sessions) == 0

    def test_update_session_none_session_id(self):
        """Test that update_session does nothing for None session_id."""
        self.cache.update_session(None, "resp_123", 5, 1000)
        assert len(self.cache._sessions) == 0

    def test_update_session_empty_response_id(self):
        """Test that update_session does nothing for empty response_id."""
        self.cache.update_session("session_123", "", 5, 1000)
        assert len(self.cache._sessions) == 0

    def test_update_session_none_response_id(self):
        """Test that update_session does nothing for None response_id."""
        self.cache.update_session("session_123", None, 5, 1000)
        assert len(self.cache._sessions) == 0

    def test_update_session_success(self):
        """Test that update_session creates a new session."""
        expire_at = time.time() + 3600
        self.cache.update_session("session_123", "resp_456", 10, expire_at)

        assert "session_123" in self.cache._sessions
        session = self.cache._sessions["session_123"]
        assert session.response_id == "resp_456"
        assert session.last_message_count == 10
        assert session.expire_at == expire_at

    def test_update_session_existing(self):
        """Test that update_session updates an existing session."""
        session_id = "existing_session"
        # Create initial session
        self.cache._sessions[session_id] = SessionData(
            response_id="resp_old",
            expire_at=time.time() + 3600,
            last_message_count=5
        )
        # Update it
        expire_at_new = time.time() + 7200
        self.cache.update_session(session_id, "resp_new", 15, expire_at_new)

        session = self.cache._sessions[session_id]
        assert session.response_id == "resp_new"
        assert session.last_message_count == 15
        assert session.expire_at == expire_at_new

    def test_invalidate_session_exists(self):
        """Test that invalidate_session removes an existing session."""
        session_id = "to_remove"
        self.cache._sessions[session_id] = SessionData(
            response_id="resp_123",
            expire_at=time.time() + 3600,
            last_message_count=5
        )
        self.cache.invalidate_session(session_id)
        assert session_id not in self.cache._sessions

    def test_invalidate_session_not_exists(self):
        """Test that invalidate_session does nothing for non-existent session."""
        initial_count = len(self.cache._sessions)
        self.cache.invalidate_session("non_existent")
        assert len(self.cache._sessions) == initial_count

    def test_singleton_pattern(self):
        """Test that CacheManager follows singleton pattern."""
        cache1 = CacheManager()
        cache2 = CacheManager()
        assert cache1 is cache2

    def test_expiration_buffer_constant(self):
        """Test that EXPIRATION_BUFFER is correctly defined."""
        assert CacheManager.EXPIRATION_BUFFER == 10
