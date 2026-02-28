import time
from typing import Dict, Optional
from pydantic import BaseModel
from nura.core.logger import logger


class SessionData(BaseModel):
    response_id: str
    expire_at: float
    last_message_count: int


class CacheManager:
    _instance = None
    _sessions: Dict[str, SessionData] = {}

    # Buffer time in seconds to consider cache expired before actual expiration
    # to avoid race conditions during request processing
    EXPIRATION_BUFFER = 10

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve a valid session from cache.
        Returns None if session doesn't exist or is expired (including buffer).
        """
        if not session_id:
            return None

        data = self._sessions.get(session_id)
        if not data:
            return None

        # Check expiration with buffer
        if time.time() > (data.expire_at - self.EXPIRATION_BUFFER):
            logger.info(f"Session {session_id} cache expired (or within buffer).")
            self.invalidate_session(session_id)
            return None

        return data

    def update_session(
        self, session_id: str, response_id: str, message_count: int, expire_at: int
    ):
        """
        Update or create a session cache entry.
        Calculates expire_at based on config.llm.default.cache_ttl.
        """
        if not session_id or not response_id:
            return

        self._sessions[session_id] = SessionData(
            response_id=response_id,
            expire_at=expire_at,
            last_message_count=message_count,
        )
        logger.debug(f"Updated session {session_id} cache: response_id={response_id}")

    def invalidate_session(self, session_id: str):
        """Remove a session from cache."""
        if session_id in self._sessions:
            del self._sessions[session_id]


cache_manager = CacheManager()
