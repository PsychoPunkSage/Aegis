"""
Caching utilities for performance optimization
"""
import time
import logging
import functools
from typing import Dict, Any, Optional

class LRUCache:
    """
    Least Recently Used (LRU) cache for function results
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items to store
        """
        self.cache = {}
        self.max_size = max_size
        self.timestamps = {}
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger(__name__)
        
    def get(self, key: str) -> Any:
        """
        Get item from cache
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value or None if not found
        """
        if key in self.cache:
            self.hits += 1
            self.timestamps[key] = time.time()
            return self.cache[key]
        else:
            self.misses += 1
            return None
            
    def set(self, key: str, value: Any) -> None:
        """
        Store item in cache
        
        Args:
            key: Cache key
            value: Value to store
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
        # Check if we need to evict items
        if len(self.cache) > self.max_size:
            # Find oldest item
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            
            # Remove it
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
            
    def clear(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        self.timestamps.clear()
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }

def memoize(maxsize: int = 128, ttl: Optional[float] = None):
    """
    Memoization decorator with time-to-live
    
    Args:
        maxsize: Maximum cache size
        ttl: Time-to-live in seconds (None for no expiry)
        
    Returns:
        Callable: Decorated function
    """
    cache = {}
    timestamps = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = str(args) + str(sorted(kwargs.items()))
            
            # Check if result is in cache and not expired
            if key in cache:
                timestamp = timestamps[key]
                if ttl is None or time.time() - timestamp < ttl:
                    return cache[key]
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Store in cache
            cache[key] = result
            timestamps[key] = time.time()
            
            # Manage cache size
            if len(cache) > maxsize:
                # Find oldest entry
                oldest_key = min(timestamps.keys(), key=lambda k: timestamps[k])
                
                # Remove it
                del cache[oldest_key]
                del timestamps[oldest_key]
                
            return result
        
        # Add cache statistics function
        def cache_info():
            return {
                "size": len(cache),
                "maxsize": maxsize,
                "ttl": ttl,
                "currsize": len(cache)
            }
        
        wrapper.cache_info = cache_info
        
        # Add cache clear function
        def cache_clear():
            cache.clear()
            timestamps.clear()
            
        wrapper.cache_clear = cache_clear
        
        return wrapper
    
    return decorator