"""SQLite-based history storage implementation."""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager

from ...models.config import HistoryConfig
from ...models.review import ReviewResult, ReviewStatus


logger = logging.getLogger(__name__)


class HistoryStorage:
    """SQLite-based storage for review history."""
    
    def __init__(self, config: HistoryConfig):
        """
        Initialize history storage.
        
        Args:
            config: History configuration
        """
        self.config = config
        
        # Use custom path or default
        if config.storage_path:
            self.db_path = Path(config.storage_path).expanduser() / "history.db"
        else:
            self.db_path = Path.home() / ".config" / "unc" / "history" / "history.db"
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config.enabled:
            self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with self._get_connection() as conn:
            # Create review history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_history (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    request_data TEXT NOT NULL,
                    diff_data TEXT,
                    issues_data TEXT NOT NULL,
                    summary TEXT,
                    recommendations TEXT,
                    metrics_data TEXT NOT NULL,
                    
                    -- Timestamps
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    
                    -- AI metadata
                    ai_provider TEXT,
                    ai_model TEXT,
                    
                    -- Error info
                    error_message TEXT,
                    
                    -- Storage metadata
                    size_bytes INTEGER,
                    file_count INTEGER
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON review_history(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON review_history(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_provider ON review_history(ai_provider)")
            
            conn.commit()
            logger.info(f"History database initialized at: {self.db_path}")
    
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
    
    def save_review(self, result: ReviewResult) -> None:
        """
        Save a review result to history.
        
        Args:
            result: Review result to save
        """
        if not self.config.enabled:
            return
            
        try:
            # Serialize complex objects to JSON
            request_data = result.request.model_dump_json() if result.request else None
            diff_data = result.diff.model_dump_json() if result.diff else None
            issues_data = json.dumps([issue.model_dump() for issue in result.issues])
            recommendations = json.dumps(result.recommendations)
            metrics_data = result.metrics.model_dump_json() if result.metrics else None
            
            # Calculate storage metadata
            size_bytes = len(issues_data.encode()) + len(request_data.encode()) if request_data else 0
            file_count = len(result.diff.files) if result.diff else 0
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO review_history 
                    (id, status, request_data, diff_data, issues_data, summary, 
                     recommendations, metrics_data, created_at, started_at, completed_at,
                     ai_provider, ai_model, error_message, size_bytes, file_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.id,
                    result.status.value,
                    request_data,
                    diff_data,
                    issues_data,
                    result.summary,
                    recommendations,
                    metrics_data,
                    result.created_at,
                    result.started_at,
                    result.completed_at,
                    result.ai_provider_used,
                    result.ai_model_used,
                    result.error_message,
                    size_bytes,
                    file_count
                ))
                conn.commit()
                
                logger.debug(f"Saved review {result.id} to history")
                
                # Cleanup old entries if needed
                self._cleanup_if_needed(conn)
                
        except Exception as e:
            logger.error(f"Failed to save review to history: {e}")
    
    def get_reviews(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get review history entries.
        
        Args:
            limit: Maximum number of reviews to return
            offset: Number of reviews to skip
            
        Returns:
            List of review history entries
        """
        if not self.config.enabled:
            return []
            
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, status, created_at, ai_provider, ai_model, 
                           summary, size_bytes, file_count, error_message,
                           (SELECT COUNT(*) FROM json_each(issues_data)) as issue_count
                    FROM review_history 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                reviews = []
                for row in cursor.fetchall():
                    reviews.append({
                        'id': row['id'],
                        'status': row['status'],
                        'created_at': row['created_at'],
                        'ai_provider': row['ai_provider'],
                        'ai_model': row['ai_model'],
                        'summary': row['summary'],
                        'file_count': row['file_count'] or 0,
                        'issue_count': row['issue_count'] or 0,
                        'error_message': row['error_message']
                    })
                    
                return reviews
                
        except Exception as e:
            logger.error(f"Failed to get reviews from history: {e}")
            return []
    
    def get_review_by_id(self, review_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific review by ID.
        
        Args:
            review_id: Review ID to retrieve
            
        Returns:
            Review data or None if not found
        """
        if not self.config.enabled:
            return None
            
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM review_history WHERE id = ?
                """, (review_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                    
                return None
                
        except Exception as e:
            logger.error(f"Failed to get review {review_id} from history: {e}")
            return None
    
    def delete_review(self, review_id: str) -> bool:
        """
        Delete a specific review from history.
        
        Args:
            review_id: Review ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if not self.config.enabled:
            return False
            
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM review_history WHERE id = ?", (review_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete review {review_id} from history: {e}")
            return False
    
    def clear_history(self) -> int:
        """
        Clear all history entries.
        
        Returns:
            Number of entries deleted
        """
        if not self.config.enabled:
            return 0
            
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM review_history")
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return 0
    
    def _cleanup_if_needed(self, conn: sqlite3.Connection) -> None:
        """Clean up old entries based on configuration."""
        try:
            # Clean up by retention days
            if self.config.retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
                cursor = conn.execute(
                    "DELETE FROM review_history WHERE created_at < ?",
                    (cutoff_date,)
                )
                if cursor.rowcount > 0:
                    logger.info(f"Cleaned up {cursor.rowcount} old history entries")
            
            # Clean up by max entries
            if self.config.max_entries > 0:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM review_history"
                )
                count = cursor.fetchone()[0]
                
                if count > self.config.max_entries:
                    excess = count - self.config.max_entries
                    cursor = conn.execute("""
                        DELETE FROM review_history 
                        WHERE id IN (
                            SELECT id FROM review_history 
                            ORDER BY created_at ASC 
                            LIMIT ?
                        )
                    """, (excess,))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Cleaned up {cursor.rowcount} excess history entries")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to cleanup history: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get history storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        if not self.config.enabled:
            return {"enabled": False}
            
        try:
            with self._get_connection() as conn:
                # Total entries
                cursor = conn.execute("SELECT COUNT(*) FROM review_history")
                total_entries = cursor.fetchone()[0]
                
                # Entries by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) 
                    FROM review_history 
                    GROUP BY status
                """)
                by_status = dict(cursor.fetchall())
                
                # Entries by provider
                cursor = conn.execute("""
                    SELECT ai_provider, COUNT(*) 
                    FROM review_history 
                    WHERE ai_provider IS NOT NULL
                    GROUP BY ai_provider
                """)
                by_provider = dict(cursor.fetchall())
                
                # Date range
                cursor = conn.execute("""
                    SELECT MIN(created_at), MAX(created_at) 
                    FROM review_history
                """)
                date_range = cursor.fetchone()
                
                return {
                    "enabled": True,
                    "total_entries": total_entries,
                    "by_status": by_status,
                    "by_provider": by_provider,
                    "date_range": {
                        "earliest": date_range[0],
                        "latest": date_range[1]
                    },
                    "storage_path": str(self.db_path)
                }
                
        except Exception as e:
            logger.error(f"Failed to get history statistics: {e}")
            return {"enabled": True, "error": str(e)} 