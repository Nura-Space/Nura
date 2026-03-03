"""Configuration for context management (turn-based compression).

DEPRECATED: This module is deprecated. Use nura.config instead.

This module is kept for backward compatibility but will be removed in a future version.
Please migrate to the new configuration system:

    Old:
        from nura.context.config import ContextConfig
        config = ContextConfig()

    New:
        from nura.config import get_config
        config = get_config()
        context_config = config.context
"""

import warnings
from dataclasses import dataclass

# Issue deprecation warning when module is imported
warnings.warn(
    "nura.context.config is deprecated and will be removed in a future version. "
    "Please use 'from nura.config import get_config' instead.",
    DeprecationWarning,
    stacklevel=2,
)


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
