"""
Simple in-memory cache with TTL (Time To Live)
"""

import time
from typing import Any, Optional, Dict, Tuple
from config import Config
from utils.logger import logger


class SimpleCache:
    """
    In-memory cache with automatic expiration
    
    Usage:
        cache = SimpleCache(ttl=300)
        cache.set('key', 'value')
        value = cache.get('key')
    """
    
    def __init__(self, ttl: int = Config.CACHE_TTL):
        """
        Initialize cache
        
        Args:
            ttl: Time to live in seconds (default from config)
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key in self.cache:
            data, timestamp = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp < self.ttl:
                logger.info(f"✨ Cache hit: {key[:50]}...")
                return data
            else:
                # Remove expired entry
                del self.cache[key]
                logger.info(f"⏰ Cache expired: {key[:50]}...")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, time.time())
        logger.info(f"💾 Cached: {key[:50]}...")
    
    def delete(self, key: str) -> bool:
        """
        Delete specific key from cache
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key existed, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
            logger.info(f"🗑️  Deleted from cache: {key[:50]}...")
            return True
        return False
    
    def clear(self) -> None:
        """Clear entire cache"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️  Cache cleared ({count} items removed)")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_items = len(self.cache)
        expired_items = sum(
            1 for _, timestamp in self.cache.values()
            if time.time() - timestamp >= self.ttl
        )
        
        return {
            "total_items": total_items,
            "active_items": total_items - expired_items,
            "expired_items": expired_items,
            "ttl_seconds": self.ttl
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache
        
        Returns:
            Number of items removed
        """
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if time.time() - timestamp >= self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)


# Global cache instance
cache = SimpleCache()