"""Issue data models for code review results."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    """Severity levels for code review issues."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    """Categories for code review issues."""
    
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    STYLE = "style"
    BUGS = "bugs"
    DESIGN = "design"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COMPLEXITY = "complexity"


class IssueLocation(BaseModel):
    """Location information for an issue in the code."""
    
    file_path: str = Field(..., description="Path to the file containing the issue")
    line_start: int = Field(..., description="Starting line number (1-indexed)")
    line_end: Optional[int] = Field(None, description="Ending line number for multi-line issues")
    column_start: Optional[int] = Field(None, description="Starting column (1-indexed)")
    column_end: Optional[int] = Field(None, description="Ending column")
    
    @property
    def line_range(self) -> str:
        """Get a human-readable line range."""
        if self.line_end and self.line_end != self.line_start:
            return f"{self.line_start}-{self.line_end}"
        return str(self.line_start)


class Issue(BaseModel):
    """Represents a single code review issue."""
    
    id: str = Field(..., description="Unique identifier for the issue")
    title: str = Field(..., description="Short title/summary of the issue")
    description: str = Field(..., description="Detailed description of the issue")
    severity: IssueSeverity = Field(..., description="Severity level of the issue")
    category: IssueCategory = Field(..., description="Category/type of the issue")
    location: IssueLocation = Field(..., description="Location of the issue in code")
    
    # Code context
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    suggested_fix: Optional[str] = Field(None, description="Suggested code fix")
    
    # Additional metadata
    confidence: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0, 
        description="AI confidence in this issue (0.0 to 1.0)"
    )
    tags: List[str] = Field(default_factory=list, description="Additional tags")
    references: List[str] = Field(
        default_factory=list, 
        description="External references (URLs, docs, etc.)"
    )
    
    # Review metadata
    detected_by: str = Field(default="ai", description="Tool/method that detected this issue")
    created_at: Optional[str] = Field(None, description="ISO timestamp when issue was created")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            IssueSeverity: lambda v: v.value,
            IssueCategory: lambda v: v.value,
        }
        
    def is_blocking(self) -> bool:
        """Check if this issue should block the review."""
        return self.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()
    
    def format_location(self) -> str:
        """Format location for display."""
        location = f"{self.location.file_path}:{self.location.line_range}"
        if self.location.column_start:
            location += f":{self.location.column_start}"
        return location 