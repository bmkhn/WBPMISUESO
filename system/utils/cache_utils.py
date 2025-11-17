"""
Cache utility functions for managing site-wide cache invalidation.
"""

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
import logging

logger = logging.getLogger(__name__)


def clear_all_cache():
    """
    Clear all cache entries.
    Use this when a significant change affects the entire site.
    """
    try:
        cache.clear()
        logger.info("All cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")


def clear_cache_by_prefix(prefix):
    """
    Clear cache entries matching a specific prefix.
    
    Args:
        prefix (str): The cache key prefix to match
    """
    try:
        # For LocMemCache, we need to clear all since it doesn't support prefix deletion
        # In production with Redis/Memcached, you could implement selective deletion
        cache.clear()
        logger.info(f"Cache cleared for prefix: {prefix}")
    except Exception as e:
        logger.error(f"Error clearing cache for prefix {prefix}: {e}")


def invalidate_related_caches(model_name, instance_id=None):
    """
    Invalidate caches related to a specific model.
    
    Args:
        model_name (str): Name of the model that changed
        instance_id: Optional ID of the specific instance
    """
    # For now, clear all cache since we're using full-site caching
    # In the future, this could be made more granular
    clear_all_cache()
    
    if instance_id:
        logger.info(f"Cache invalidated for {model_name} (ID: {instance_id})")
    else:
        logger.info(f"Cache invalidated for {model_name}")
