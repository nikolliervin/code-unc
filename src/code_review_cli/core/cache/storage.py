"""SQLite-based cache storage implementation."""

import sqlite3
import json
import logging
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from contextlib import contextmanager

from ...models.config import CacheConfig


logger = logging.getLogger(__name__)


class CacheStorage:
    """SQLite-based cache storage for AI responses and git operations."""
    
    def __init__(self, config: CacheConfig):
        """
        Initialize cache storage.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.db_path = Path(config.cache_directory).expanduser() / "cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with self._get_connection() as conn:
            # Create cache entries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    metadata TEXT,
                    size_bytes INTEGER NOT NULL
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON cache_entries(key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operation_type ON cache_entries(operation_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)")
            
            # Create cache statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    last_updated TIMESTAMP NOT NULL,
                    UNIQUE(operation_type)
                )
            """)
            
            conn.commit()
            logger.info(f"Cache database initialized at: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _generate_key(self, operation_type: str, **params) -> str:
        """
        Generate a cache key from operation type and parameters.
        
        Args:
            operation_type: Type of operation (e.g., 'git_diff', 'ai_response')
            **params: Parameters that uniquely identify the operation
            
        Returns:
            Generated cache key
        """
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, sort_keys=True)
        
        # Create hash of operation type and parameters
        content = f"{operation_type}:{param_str}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, operation_type: str, **params) -> Optional[Any]:
        """
        Get cached value for operation.
        
        Args:
            operation_type: Type of operation
            **params: Operation parameters
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.config.enabled:
            return None
        
        key = self._generate_key(operation_type, **params)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM cache_entries WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row is None:
                self._record_cache_miss(operation_type)
                return None
            
            # Check if expired
            expires_at = row['expires_at']
            if datetime.now() > expires_at:
                # Remove expired entry
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                self._record_cache_miss(operation_type)
                return None
            
            # Deserialize value
            try:
                value = json.loads(row['value'])
                self._record_cache_hit(operation_type)
                logger.debug(f"Cache hit for {operation_type}")
                return value
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to deserialize cached value: {e}")
                # Remove corrupted entry
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                self._record_cache_miss(operation_type)
                return None
    
    def set(
        self,
        operation_type: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **params
    ) -> None:
        """
        Store value in cache.
        
        Args:
            operation_type: Type of operation
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses config default if None)
            metadata: Additional metadata to store
            **params: Operation parameters
        """
        if not self.config.enabled:
            return
        
        # Determine TTL
        if ttl_seconds is None:
            ttl_map = {
                "git_diff": self.config.git_diff_ttl,
                "ai_response": self.config.ai_response_ttl,
            }
            ttl_seconds = ttl_map.get(operation_type, 3600)  # Default 1 hour
        
        if ttl_seconds <= 0:
            return  # Don't cache if TTL is 0 or negative
        
        key = self._generate_key(operation_type, **params)
        
        # Serialize value
        try:
            serialized_value = json.dumps(value, default=self._json_serializer)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize value for caching: {e}")
            return
        
        # Calculate size and expiration
        size_bytes = len(serialized_value.encode('utf-8'))
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # Serialize metadata
        metadata_str = json.dumps(metadata) if metadata else None
        
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, operation_type, created_at, expires_at, metadata, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    key,
                    serialized_value,
                    operation_type,
                    datetime.now(),
                    expires_at,
                    metadata_str,
                    size_bytes
                ))
                conn.commit()
                logger.debug(f"Cached {operation_type} with TTL {ttl_seconds}s")
                
                # Check if we need to cleanup based on size
                self._cleanup_if_needed(conn)
                
            except sqlite3.Error as e:
                logger.error(f"Failed to cache value: {e}")
    
    def delete(self, operation_type: str, **params) -> bool:
        """
        Delete cached value.
        
        Args:
            operation_type: Type of operation
            **params: Operation parameters
            
        Returns:
            True if value was deleted, False if not found
        """
        key = self._generate_key(operation_type, **params)
        
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self, operation_type: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            operation_type: Type to clear (clears all if None)
            
        Returns:
            Number of entries deleted
        """
        with self._get_connection() as conn:
            if operation_type:
                cursor = conn.execute(
                    "DELETE FROM cache_entries WHERE operation_type = ?",
                    (operation_type,)
                )
            else:
                cursor = conn.execute("DELETE FROM cache_entries")
            
            conn.commit()
            deleted_count = cursor.rowcount
            
            logger.info(f"Cleared {deleted_count} cache entries" + 
                       (f" for {operation_type}" if operation_type else ""))
            return deleted_count
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at < ?",
                (datetime.now(),)
            )
            conn.commit()
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
            
            return deleted_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._get_connection() as conn:
            # Overall stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(size_bytes) as total_size_bytes,
                    COUNT(CASE WHEN expires_at > ? THEN 1 END) as active_entries,
                    COUNT(CASE WHEN expires_at <= ? THEN 1 END) as expired_entries
                FROM cache_entries
            """, (datetime.now(), datetime.now()))
            
            overall = cursor.fetchone()
            
            # Per-operation stats
            cursor = conn.execute("""
                SELECT operation_type, cache_hits, cache_misses, total_requests
                FROM cache_stats
            """)
            
            operation_stats = {
                row['operation_type']: {
                    'hits': row['cache_hits'],
                    'misses': row['cache_misses'],
                    'total_requests': row['total_requests'],
                    'hit_rate': row['cache_hits'] / max(row['total_requests'], 1)
                }
                for row in cursor.fetchall()
            }
            
            return {
                'total_entries': overall['total_entries'],
                'active_entries': overall['active_entries'],
                'expired_entries': overall['expired_entries'],
                'total_size_bytes': overall['total_size_bytes'] or 0,
                'total_size_mb': (overall['total_size_bytes'] or 0) / (1024 * 1024),
                'operation_stats': operation_stats,
            }
    
    def _cleanup_if_needed(self, conn: sqlite3.Connection) -> None:
        """Clean up cache if size exceeds limit."""
        # Check current size
        cursor = conn.execute("SELECT SUM(size_bytes) as total_size FROM cache_entries")
        total_size = cursor.fetchone()['total_size'] or 0
        
        max_size_bytes = self.config.max_cache_size_mb * 1024 * 1024
        
        if total_size > max_size_bytes:
            # Remove oldest entries until under limit
            target_size = max_size_bytes * 0.8  # Clean to 80% of limit
            
            cursor = conn.execute("""
                DELETE FROM cache_entries 
                WHERE id IN (
                    SELECT id FROM cache_entries 
                    ORDER BY created_at ASC 
                    LIMIT (
                        SELECT COUNT(*) FROM cache_entries 
                        WHERE (SELECT SUM(size_bytes) FROM cache_entries) > ?
                    )
                )
            """, (target_size,))
            
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(f"Cache cleanup: removed {deleted} entries to free space")
    
    def _record_cache_hit(self, operation_type: str) -> None:
        """Record a cache hit for statistics."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_stats 
                (operation_type, cache_hits, cache_misses, total_requests, last_updated)
                VALUES (
                    ?,
                    COALESCE((SELECT cache_hits FROM cache_stats WHERE operation_type = ?), 0) + 1,
                    COALESCE((SELECT cache_misses FROM cache_stats WHERE operation_type = ?), 0),
                    COALESCE((SELECT total_requests FROM cache_stats WHERE operation_type = ?), 0) + 1,
                    ?
                )
            """, (operation_type, operation_type, operation_type, operation_type, datetime.now()))
            conn.commit()
    
    def _record_cache_miss(self, operation_type: str) -> None:
        """Record a cache miss for statistics."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache_stats 
                (operation_type, cache_hits, cache_misses, total_requests, last_updated)
                VALUES (
                    ?,
                    COALESCE((SELECT cache_hits FROM cache_stats WHERE operation_type = ?), 0),
                    COALESCE((SELECT cache_misses FROM cache_stats WHERE operation_type = ?), 0) + 1,
                    COALESCE((SELECT total_requests FROM cache_stats WHERE operation_type = ?), 0) + 1,
                    ?
                )
            """, (operation_type, operation_type, operation_type, operation_type, datetime.now()))
            conn.commit()
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj) 