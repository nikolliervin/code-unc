"""Review data models for code review operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from .issue import Issue, IssueSeverity
from .diff import GitDiff


class ReviewStatus(str, Enum):
    """Status of a code review."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewFocus(str, Enum):
    """Focus areas for code review."""
    
    GENERAL = "general"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BUGS = "bugs"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"


class ReviewRequest(BaseModel):
    """Request for a code review."""
    
    # Git information
    source_branch: Optional[str] = Field(None, description="Source branch (defaults to current)")
    target_branch: str = Field("main", description="Target branch to compare against")
    commit_hash: Optional[str] = Field(None, description="Specific commit to review")
    
    # Review parameters
    focus: ReviewFocus = Field(ReviewFocus.GENERAL, description="Primary focus area")
    include_patterns: List[str] = Field(default_factory=list, description="File patterns to include")
    exclude_patterns: List[str] = Field(default_factory=list, description="File patterns to exclude")
    max_files: int = Field(50, description="Maximum number of files to review")
    
    # AI parameters
    ai_provider: Optional[str] = Field(None, description="AI provider to use")
    ai_model: Optional[str] = Field(None, description="AI model to use")
    temperature: float = Field(0.2, ge=0.0, le=2.0, description="AI temperature setting")
    
    # Output options
    output_format: str = Field("rich", description="Output format (rich, json, markdown)")
    save_to_history: bool = Field(True, description="Save review to history")
    
    # Additional context
    context: Optional[str] = Field(None, description="Additional context for the review")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt to use")


class ReviewMetrics(BaseModel):
    """Metrics and statistics from a code review."""
    
    # Issue counts by severity
    critical_issues: int = Field(default=0, description="Number of critical issues")
    high_issues: int = Field(default=0, description="Number of high severity issues")
    medium_issues: int = Field(default=0, description="Number of medium severity issues")
    low_issues: int = Field(default=0, description="Number of low severity issues")
    info_issues: int = Field(default=0, description="Number of info-level issues")
    
    # File statistics
    files_reviewed: int = Field(default=0, description="Number of files reviewed")
    lines_added: int = Field(default=0, description="Total lines added")
    lines_deleted: int = Field(default=0, description="Total lines deleted")
    
    # Performance metrics
    review_duration: Optional[float] = Field(None, description="Review duration in seconds")
    ai_api_calls: int = Field(default=0, description="Number of AI API calls made")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost in USD")
    
    @property
    def total_issues(self) -> int:
        """Get total number of issues."""
        return (
            self.critical_issues + self.high_issues + self.medium_issues + 
            self.low_issues + self.info_issues
        )
    
    @property
    def blocking_issues(self) -> int:
        """Get number of blocking issues (critical + high)."""
        return self.critical_issues + self.high_issues
    
    @property
    def total_changes(self) -> int:
        """Get total number of line changes."""
        return self.lines_added + self.lines_deleted
    
    def calculate_score(self) -> float:
        """Calculate a review score (0-100) based on issues found."""
        if self.total_issues == 0:
            return 100.0
        
        # Weight issues by severity
        weighted_issues = (
            self.critical_issues * 10 +
            self.high_issues * 5 +
            self.medium_issues * 2 +
            self.low_issues * 1 +
            self.info_issues * 0.5
        )
        
        # Calculate score relative to lines of code
        if self.total_changes == 0:
            return max(0, 100 - weighted_issues)
        
        issue_density = weighted_issues / self.total_changes * 100
        return max(0, 100 - issue_density)


class ReviewResult(BaseModel):
    """Result of a code review operation."""
    
    # Basic information
    id: str = Field(..., description="Unique review identifier")
    status: ReviewStatus = Field(..., description="Current status of the review")
    
    # Request information
    request: ReviewRequest = Field(..., description="Original review request")
    
    # Review content
    diff: Optional[GitDiff] = Field(None, description="Git diff that was reviewed")
    issues: List[Issue] = Field(default_factory=list, description="Issues found during review")
    summary: Optional[str] = Field(None, description="Overall review summary")
    recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    
    # Metrics
    metrics: ReviewMetrics = Field(default_factory=ReviewMetrics, description="Review metrics")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When review was created")
    started_at: Optional[datetime] = Field(None, description="When review started")
    completed_at: Optional[datetime] = Field(None, description="When review completed")
    
    # AI information
    ai_provider_used: Optional[str] = Field(None, description="AI provider that was used")
    ai_model_used: Optional[str] = Field(None, description="AI model that was used")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if review failed")
    
    def calculate_metrics(self) -> None:
        """Calculate metrics from issues and diff."""
        # Count issues by severity
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        self.metrics.critical_issues = severity_counts.get(IssueSeverity.CRITICAL, 0)
        self.metrics.high_issues = severity_counts.get(IssueSeverity.HIGH, 0)
        self.metrics.medium_issues = severity_counts.get(IssueSeverity.MEDIUM, 0)
        self.metrics.low_issues = severity_counts.get(IssueSeverity.LOW, 0)
        self.metrics.info_issues = severity_counts.get(IssueSeverity.INFO, 0)
        
        # Calculate file and line metrics from diff
        if self.diff:
            self.metrics.files_reviewed = len(self.diff.files)
            self.metrics.lines_added = self.diff.total_additions
            self.metrics.lines_deleted = self.diff.total_deletions
        
        # Calculate duration if both timestamps exist
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.metrics.review_duration = duration
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[Issue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_blocking_issues(self) -> List[Issue]:
        """Get all blocking issues (critical and high severity)."""
        return [
            issue for issue in self.issues 
            if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
        ]
    
    def is_approved(self) -> bool:
        """Check if the review should be approved (no blocking issues)."""
        return len(self.get_blocking_issues()) == 0
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to a summary dictionary for display."""
        return {
            "id": self.id,
            "status": self.status.value,
            "total_issues": self.metrics.total_issues,
            "blocking_issues": self.metrics.blocking_issues,
            "files_reviewed": self.metrics.files_reviewed,
            "score": self.metrics.calculate_score(),
            "approved": self.is_approved(),
            "created_at": self.created_at.isoformat(),
            "duration": self.metrics.review_duration,
        }


class Review(BaseModel):
    """Complete review representation combining request and result."""
    
    request: ReviewRequest = Field(..., description="Review request")
    result: Optional[ReviewResult] = Field(None, description="Review result (if completed)")
    
    @property
    def is_completed(self) -> bool:
        """Check if the review is completed."""
        return (
            self.result is not None and 
            self.result.status == ReviewStatus.COMPLETED
        )
    
    @property
    def is_approved(self) -> bool:
        """Check if the review is approved."""
        return self.result is not None and self.result.is_approved()
    
    def get_status(self) -> ReviewStatus:
        """Get the current status of the review."""
        if self.result:
            return self.result.status
        return ReviewStatus.PENDING 