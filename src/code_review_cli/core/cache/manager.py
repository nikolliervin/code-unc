"""Cache manager for high-level cache operations."""

import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import threading

from .storage import CacheStorage
from ...models.config import CacheConfig
from ...models.diff import GitDiff
from ...models.review import ReviewResult


logger = logging.getLogger(__name__)


class CacheManager:
    """High-level cache manager for AI responses and git operations."""
    
    def __init__(self, config: CacheConfig):
        """
        Initialize cache manager.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.storage = CacheStorage(config)
        self._cleanup_lock = threading.Lock()
        self._last_cleanup = datetime.now()
    
    def get_git_diff(
        self,
        source_branch: str,
        target_branch: str,
        repository: str,
        file_paths: Optional[list] = None,
    ) -> Optional[GitDiff]:
        """
        Get cached git diff.
        
        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            repository: Repository identifier
            file_paths: List of file paths (for cache key)
            
        Returns:
            Cached GitDiff or None
        """
        cached_data = self.storage.get(
            "git_diff",
            source_branch=source_branch,
            target_branch=target_branch,
            repository=repository,
            file_paths=file_paths or [],
        )
        
        if cached_data:
            try:
                return GitDiff(**cached_data)
            except Exception as e:
                logger.warning(f"Failed to deserialize cached git diff: {e}")
                return None
        
        return None
    
    def cache_git_diff(
        self,
        git_diff: GitDiff,
        source_branch: str,
        target_branch: str,
        repository: str,
        file_paths: Optional[list] = None,
    ) -> None:
        """
        Cache git diff data.
        
        Args:
            git_diff: GitDiff object to cache
            source_branch: Source branch name
            target_branch: Target branch name
            repository: Repository identifier
            file_paths: List of file paths (for cache key)
        """
        self.storage.set(
            "git_diff",
            git_diff.dict(),
            metadata={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "repository": repository,
                "file_count": len(git_diff.files),
            },
            source_branch=source_branch,
            target_branch=target_branch,
            repository=repository,
            file_paths=file_paths or [],
        )
    
    def get_ai_response(
        self,
        diff_hash: str,
        prompt_hash: str,
        ai_provider: str,
        ai_model: str,
        focus: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached AI response.
        
        Args:
            diff_hash: Hash of the diff content
            prompt_hash: Hash of the prompt
            ai_provider: AI provider name
            ai_model: AI model name
            focus: Review focus area
            
        Returns:
            Cached AI response or None
        """
        return self.storage.get(
            "ai_response",
            diff_hash=diff_hash,
            prompt_hash=prompt_hash,
            ai_provider=ai_provider,
            ai_model=ai_model,
            focus=focus,
        )
    
    def cache_ai_response(
        self,
        response_data: Dict[str, Any],
        diff_hash: str,
        prompt_hash: str,
        ai_provider: str,
        ai_model: str,
        focus: str,
        cost_estimate: Optional[float] = None,
    ) -> None:
        """
        Cache AI response data.
        
        Args:
            response_data: AI response to cache
            diff_hash: Hash of the diff content
            prompt_hash: Hash of the prompt
            ai_provider: AI provider name
            ai_model: AI model name
            focus: Review focus area
            cost_estimate: Cost estimate for the request
        """
        self.storage.set(
            "ai_response",
            response_data,
            metadata={
                "ai_provider": ai_provider,
                "ai_model": ai_model,
                "focus": focus,
                "cost_estimate": cost_estimate,
                "cached_at": datetime.now().isoformat(),
            },
            diff_hash=diff_hash,
            prompt_hash=prompt_hash,
            ai_provider=ai_provider,
            ai_model=ai_model,
            focus=focus,
        )
    
    def get_review_result(self, review_id: str) -> Optional[ReviewResult]:
        """
        Get cached review result.
        
        Args:
            review_id: Review identifier
            
        Returns:
            Cached ReviewResult or None
        """
        cached_data = self.storage.get("review_result", review_id=review_id)
        
        if cached_data:
            try:
                return ReviewResult(**cached_data)
            except Exception as e:
                logger.warning(f"Failed to deserialize cached review result: {e}")
                return None
        
        return None
    
    def cache_review_result(
        self,
        review_result: ReviewResult,
        ttl_days: int = 30,
    ) -> None:
        """
        Cache complete review result.
        
        Args:
            review_result: ReviewResult to cache
            ttl_days: Time to live in days
        """
        self.storage.set(
            "review_result",
            review_result.dict(),
            ttl_seconds=ttl_days * 24 * 3600,
            metadata={
                "review_id": review_result.id,
                "status": review_result.status.value,
                "total_issues": review_result.metrics.total_issues,
                "quality_score": review_result.metrics.calculate_score(),
            },
            review_id=review_result.id,
        )
    
    def invalidate_git_diff(
        self,
        source_branch: str,
        target_branch: str,
        repository: str,
    ) -> bool:
        """
        Invalidate cached git diff data.
        
        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            repository: Repository identifier
            
        Returns:
            True if cache was invalidated
        """
        return self.storage.delete(
            "git_diff",
            source_branch=source_branch,
            target_branch=target_branch,
            repository=repository,
        )
    
    def invalidate_ai_responses(self, ai_provider: Optional[str] = None) -> int:
        """
        Invalidate AI response cache.
        
        Args:
            ai_provider: Specific provider to invalidate (all if None)
            
        Returns:
            Number of entries invalidated
        """
        if ai_provider:
            # We can't easily filter by provider in the current storage design
            # This would require a more complex query system
            logger.warning("Provider-specific invalidation not fully implemented")
            return 0
        else:
            return self.storage.clear("ai_response")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        stats = self.storage.get_stats()
        
        # Add configuration info
        stats['config'] = {
            'enabled': self.config.enabled,
            'max_size_mb': self.config.max_cache_size_mb,
            'git_diff_ttl_hours': self.config.git_diff_ttl / 3600,
            'ai_response_ttl_hours': self.config.ai_response_ttl / 3600,
        }
        
        return stats
    
    def cleanup_cache(self, force: bool = False) -> Dict[str, int]:
        """
        Perform cache cleanup operations.
        
        Args:
            force: Force cleanup even if not due
            
        Returns:
            Dictionary with cleanup results
        """
        with self._cleanup_lock:
            now = datetime.now()
            cleanup_interval = timedelta(hours=self.config.cleanup_interval_hours)
            
            if not force and (now - self._last_cleanup) < cleanup_interval:
                return {"skipped": True, "expired_removed": 0}
            
            # Remove expired entries
            expired_removed = self.storage.cleanup_expired()
            
            self._last_cleanup = now
            
            return {
                "skipped": False,
                "expired_removed": expired_removed,
                "last_cleanup": now.isoformat(),
            }
    
    def optimize_cache(self) -> Dict[str, Any]:
        """
        Perform cache optimization operations.
        
        Returns:
            Dictionary with optimization results
        """
        # Get current stats
        initial_stats = self.storage.get_stats()
        
        # Clean up expired entries
        cleanup_results = self.cleanup_cache(force=True)
        
        # Get updated stats
        final_stats = self.storage.get_stats()
        
        return {
            "initial_entries": initial_stats["total_entries"],
            "final_entries": final_stats["total_entries"],
            "entries_removed": initial_stats["total_entries"] - final_stats["total_entries"],
            "size_before_mb": initial_stats["total_size_mb"],
            "size_after_mb": final_stats["total_size_mb"],
            "space_freed_mb": initial_stats["total_size_mb"] - final_stats["total_size_mb"],
            "cleanup_results": cleanup_results,
        }
    
    def clear_all_cache(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        return self.storage.clear()
    
    def clear_cache_by_type(self, operation_type: str) -> int:
        """
        Clear cache entries by operation type.
        
        Args:
            operation_type: Type of operations to clear
            
        Returns:
            Number of entries cleared
        """
        return self.storage.clear(operation_type)
    
    def is_cache_healthy(self) -> Dict[str, Any]:
        """
        Check cache health and performance.
        
        Returns:
            Cache health report
        """
        stats = self.get_cache_stats()
        
        # Calculate health metrics
        health_report = {
            "healthy": True,
            "issues": [],
            "recommendations": [],
        }
        
        # Check size
        if stats["total_size_mb"] > self.config.max_cache_size_mb * 0.9:
            health_report["healthy"] = False
            health_report["issues"].append("Cache size near limit")
            health_report["recommendations"].append("Consider clearing old entries or increasing cache size")
        
        # Check hit rates
        for op_type, op_stats in stats.get("operation_stats", {}).items():
            hit_rate = op_stats.get("hit_rate", 0)
            if hit_rate < 0.3 and op_stats.get("total_requests", 0) > 10:
                health_report["issues"].append(f"Low hit rate for {op_type}: {hit_rate:.1%}")
                health_report["recommendations"].append(f"Consider increasing TTL for {op_type}")
        
        # Check expired entries
        expired_ratio = stats.get("expired_entries", 0) / max(stats.get("total_entries", 1), 1)
        if expired_ratio > 0.3:
            health_report["issues"].append(f"High expired entry ratio: {expired_ratio:.1%}")
            health_report["recommendations"].append("Run cache cleanup more frequently")
        
        if health_report["issues"]:
            health_report["healthy"] = False
        
        return health_report
    
    def export_cache_report(self) -> Dict[str, Any]:
        """
        Export comprehensive cache report.
        
        Returns:
            Detailed cache report
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_cache_stats(),
            "health": self.is_cache_healthy(),
            "config": {
                "enabled": self.config.enabled,
                "cache_directory": self.config.cache_directory,
                "max_size_mb": self.config.max_cache_size_mb,
                "git_diff_ttl": self.config.git_diff_ttl,
                "ai_response_ttl": self.config.ai_response_ttl,
                "cleanup_interval_hours": self.config.cleanup_interval_hours,
            },
        } 