"""Cache factory for creating cache instances."""

from typing import Optional

from nura.llm.cache.ark import ArkCache
from nura.llm.cache.base import BaseCache


class CacheFactory:
    """Factory class for creating cache instances."""

    _cache_classes = [ArkCache]

    @classmethod
    def get_cache(cls, base_url: Optional[str] = None) -> Optional[BaseCache]:
        """Get cache instance based on base_url.

        Args:
            base_url: The API base URL

        Returns:
            Cache instance or None if no cache supports this URL
        """
        for cache_class in cls._cache_classes:
            cache = cache_class()
            if cache.supports_cache(base_url):
                return cache
        return None
