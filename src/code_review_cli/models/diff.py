"""Git diff data models."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Types of changes in a diff."""
    
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"
    COPIED = "copied"


class DiffLine(BaseModel):
    """Represents a single line in a diff."""
    
    line_number: Optional[int] = Field(None, description="Line number in the file")
    old_line_number: Optional[int] = Field(None, description="Line number in old file")
    new_line_number: Optional[int] = Field(None, description="Line number in new file")
    content: str = Field(..., description="Content of the line")
    line_type: str = Field(..., description="Type of line ('+', '-', ' ', etc.)")
    
    @property
    def is_addition(self) -> bool:
        """Check if this line is an addition."""
        return self.line_type == "+"
    
    @property
    def is_deletion(self) -> bool:
        """Check if this line is a deletion."""
        return self.line_type == "-"
    
    @property
    def is_context(self) -> bool:
        """Check if this line is context (unchanged)."""
        return self.line_type == " "


class DiffHunk(BaseModel):
    """Represents a hunk (section) of a diff."""
    
    old_start: int = Field(..., description="Starting line in old file")
    old_count: int = Field(..., description="Number of lines in old file")
    new_start: int = Field(..., description="Starting line in new file")
    new_count: int = Field(..., description="Number of lines in new file")
    section_header: Optional[str] = Field(None, description="Section header (e.g., function name)")
    lines: List[DiffLine] = Field(default_factory=list, description="Lines in this hunk")
    
    @property
    def header(self) -> str:
        """Generate hunk header in git format."""
        header = f"@@ -{self.old_start},{self.old_count} +{self.new_start},{self.new_count} @@"
        if self.section_header:
            header += f" {self.section_header}"
        return header
    
    @property
    def added_lines(self) -> List[DiffLine]:
        """Get all added lines in this hunk."""
        return [line for line in self.lines if line.is_addition]
    
    @property
    def deleted_lines(self) -> List[DiffLine]:
        """Get all deleted lines in this hunk."""
        return [line for line in self.lines if line.is_deletion]
    
    @property
    def context_lines(self) -> List[DiffLine]:
        """Get all context lines in this hunk."""
        return [line for line in self.lines if line.is_context]


class DiffStats(BaseModel):
    """Statistics about changes in a diff."""
    
    additions: int = Field(default=0, description="Number of lines added")
    deletions: int = Field(default=0, description="Number of lines deleted")
    changes: int = Field(default=0, description="Total number of changes")
    
    @property
    def net_change(self) -> int:
        """Calculate net change (additions - deletions)."""
        return self.additions - self.deletions
    
    @property
    def total_changes(self) -> int:
        """Calculate total changes (additions + deletions)."""
        return self.additions + self.deletions


class DiffFile(BaseModel):
    """Represents a single file in a git diff."""
    
    old_path: Optional[str] = Field(None, description="Path in old version (None for new files)")
    new_path: Optional[str] = Field(None, description="Path in new version (None for deleted files)")
    change_type: ChangeType = Field(..., description="Type of change")
    binary: bool = Field(default=False, description="Whether file is binary")
    
    # File metadata
    old_mode: Optional[str] = Field(None, description="File mode in old version")
    new_mode: Optional[str] = Field(None, description="File mode in new version")
    old_hash: Optional[str] = Field(None, description="Git hash of old file")
    new_hash: Optional[str] = Field(None, description="Git hash of new file")
    
    # Diff content
    hunks: List[DiffHunk] = Field(default_factory=list, description="Diff hunks for this file")
    stats: DiffStats = Field(default_factory=DiffStats, description="Change statistics")
    
    # Additional metadata
    language: Optional[str] = Field(None, description="Programming language detected")
    size_change: Optional[int] = Field(None, description="Change in file size (bytes)")
    
    @property
    def path(self) -> str:
        """Get the relevant file path."""
        return self.new_path or self.old_path or "unknown"
    
    @property
    def is_new_file(self) -> bool:
        """Check if this is a new file."""
        return self.change_type == ChangeType.ADDED or self.old_path is None
    
    @property
    def is_deleted_file(self) -> bool:
        """Check if this is a deleted file."""
        return self.change_type == ChangeType.DELETED or self.new_path is None
    
    @property
    def is_renamed(self) -> bool:
        """Check if this file was renamed."""
        return self.change_type == ChangeType.RENAMED
    
    @property
    def is_modified(self) -> bool:
        """Check if this file was modified."""
        return self.change_type == ChangeType.MODIFIED
    
    def get_extension(self) -> Optional[str]:
        """Get file extension."""
        path = self.path
        if '.' in path:
            return path.split('.')[-1].lower()
        return None
    
    def calculate_stats(self) -> None:
        """Calculate statistics from hunks."""
        additions = sum(len(hunk.added_lines) for hunk in self.hunks)
        deletions = sum(len(hunk.deleted_lines) for hunk in self.hunks)
        self.stats = DiffStats(
            additions=additions,
            deletions=deletions,
            changes=additions + deletions
        )


class GitDiff(BaseModel):
    """Represents a complete git diff."""
    
    source_branch: Optional[str] = Field(None, description="Source branch name")
    target_branch: str = Field(..., description="Target branch name")
    commit_hash: Optional[str] = Field(None, description="Specific commit hash")
    
    # Files in the diff
    files: List[DiffFile] = Field(default_factory=list, description="Files changed in this diff")
    
    # Overall statistics
    total_files: int = Field(default=0, description="Total number of files changed")
    total_additions: int = Field(default=0, description="Total lines added")
    total_deletions: int = Field(default=0, description="Total lines deleted")
    
    # Metadata
    created_at: Optional[str] = Field(None, description="ISO timestamp when diff was created")
    repository: Optional[str] = Field(None, description="Repository name or URL")
    
    def calculate_totals(self) -> None:
        """Calculate total statistics from all files."""
        self.total_files = len(self.files)
        self.total_additions = sum(file.stats.additions for file in self.files)
        self.total_deletions = sum(file.stats.deletions for file in self.files)
    
    def get_files_by_extension(self, extension: str) -> List[DiffFile]:
        """Get files with specific extension."""
        return [f for f in self.files if f.get_extension() == extension.lower()]
    
    def get_files_by_change_type(self, change_type: ChangeType) -> List[DiffFile]:
        """Get files with specific change type."""
        return [f for f in self.files if f.change_type == change_type]
    
    @property
    def modified_files(self) -> List[DiffFile]:
        """Get only modified files (excluding new/deleted)."""
        return [f for f in self.files if f.is_modified]
    
    @property
    def new_files(self) -> List[DiffFile]:
        """Get only new files."""
        return [f for f in self.files if f.is_new_file]
    
    @property
    def deleted_files(self) -> List[DiffFile]:
        """Get only deleted files."""
        return [f for f in self.files if f.is_deleted_file]
    
    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of the diff."""
        return {
            "total_files": self.total_files,
            "total_additions": self.total_additions,
            "total_deletions": self.total_deletions,
            "net_change": self.total_additions - self.total_deletions,
            "new_files": len(self.new_files),
            "deleted_files": len(self.deleted_files),
            "modified_files": len(self.modified_files),
            "binary_files": len([f for f in self.files if f.binary]),
        } 