"""Configuration for context management (turn-based compression)."""

from dataclasses import dataclass


@dataclass
class ContextConfig:
    """Configuration for context management (turn-based compression)

    New turn-based compression scheme:
    - Trigger threshold: 50% token (64000 for 128000 context)
    - Keep recent 10 conversation turns (not messages)
    - Compress everything before the 10th turn using LLM summarization
    """

    # Context window size
    max_tokens: int = 128000

    # Compress when token count reaches this threshold (0.5 = 50%)
    compress_threshold: float = 0.5

    # Keep recent N conversation turns
    keep_turns: int = 10

    # Minimum seconds between compressions
    compress_cooldown: int = 60

    @property
    def compress_tokens(self) -> int:
        """Trigger compression when token count reaches this (max_tokens * compress_threshold)"""
        return int(self.max_tokens * self.compress_threshold)
