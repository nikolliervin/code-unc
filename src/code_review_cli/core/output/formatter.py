"""Output formatting utilities for code review results."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ...models.review import ReviewResult
from ...models.config import OutputConfig


logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats code review results for different output types."""
    
    def __init__(self, config: OutputConfig):
        """
        Initialize output formatter.
        
        Args:
            config: Output configuration
        """
        self.config = config
    
    def format_review(
        self,
        review_result: ReviewResult,
        format_type: Optional[str] = None,
    ) -> str:
        """
        Format review result for output.
        
        Args:
            review_result: Review result to format
            format_type: Output format (overrides config default)
            
        Returns:
            Formatted output string
        """
        output_format = format_type or self.config.default_format
        
        if output_format == "json":
            return self._format_json(review_result)
        elif output_format == "markdown":
            return self._format_markdown(review_result)
        elif output_format == "html":
            return self._format_html(review_result)
        elif output_format == "rich":
            # Rich formatting is handled by ReviewConsole
            return self._format_json(review_result)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _format_json(self, review_result: ReviewResult) -> str:
        """Format as JSON."""
        data = review_result.dict()
        return json.dumps(data, indent=2, default=self._json_serializer)
    
    def _format_markdown(self, review_result: ReviewResult) -> str:
        """Format as Markdown."""
        lines = []
        
        # Header
        lines.append(f"# Code Review Report")
        lines.append(f"**ID:** {review_result.id}")
        lines.append(f"**Status:** {review_result.status.value}")
        lines.append(f"**Created:** {review_result.created_at.isoformat()}")
        lines.append("")
        
        # Summary
        if review_result.summary:
            lines.append("## Summary")
            lines.append(review_result.summary)
            lines.append("")
        
        # Metrics
        lines.append("## Metrics")
        metrics = review_result.metrics
        lines.append(f"- **Files Reviewed:** {metrics.files_reviewed}")
        lines.append(f"- **Lines Added:** {metrics.lines_added}")
        lines.append(f"- **Lines Deleted:** {metrics.lines_deleted}")
        lines.append(f"- **Total Issues:** {metrics.total_issues}")
        lines.append(f"- **Critical:** {metrics.critical_issues}")
        lines.append(f"- **High:** {metrics.high_issues}")
        lines.append(f"- **Medium:** {metrics.medium_issues}")
        lines.append(f"- **Low:** {metrics.low_issues}")
        lines.append(f"- **Info:** {metrics.info_issues}")
        lines.append("")
        
        # Score
        score = metrics.calculate_score()
        lines.append(f"**Quality Score:** {score:.1f}/100")
        lines.append("")
        
        # Issues by severity
        if review_result.issues:
            # Group issues by severity
            severity_groups = {}
            for issue in review_result.issues:
                severity = issue.severity.value
                if severity not in severity_groups:
                    severity_groups[severity] = []
                severity_groups[severity].append(issue)
            
            # Output each severity group
            for severity in ["critical", "high", "medium", "low", "info"]:
                if severity in severity_groups:
                    issues = severity_groups[severity]
                    lines.append(f"## {severity.title()} Issues ({len(issues)})")
                    lines.append("")
                    
                    for issue in issues:
                        lines.append(f"### {issue.title}")
                        lines.append(f"**File:** `{issue.location.file_path}:{issue.location.line_range}`")
                        lines.append(f"**Category:** {issue.category.value}")
                        lines.append(f"**Confidence:** {issue.confidence:.1%}")
                        lines.append("")
                        lines.append(issue.description)
                        lines.append("")
                        
                        if issue.code_snippet:
                            lines.append("**Code:**")
                            lines.append("```")
                            lines.append(issue.code_snippet)
                            lines.append("```")
                            lines.append("")
                        
                        if issue.suggested_fix:
                            lines.append("**Suggested Fix:**")
                            lines.append("```")
                            lines.append(issue.suggested_fix)
                            lines.append("```")
                            lines.append("")
                        
                        if issue.references:
                            lines.append("**References:**")
                            for ref in issue.references:
                                lines.append(f"- {ref}")
                            lines.append("")
                        
                        lines.append("---")
                        lines.append("")
        
        # Recommendations
        if review_result.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(review_result.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append(f"*Generated by Code Review CLI at {datetime.now().isoformat()}*")
        
        return "\n".join(lines)
    
    def _format_html(self, review_result: ReviewResult) -> str:
        """Format as HTML."""
        html_parts = []
        
        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Code Review Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #e1e4e8; padding-bottom: 20px; margin-bottom: 30px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; }
        .issue { border: 1px solid #e1e4e8; border-radius: 6px; margin: 15px 0; padding: 20px; }
        .issue.critical { border-left: 4px solid #d73a49; }
        .issue.high { border-left: 4px solid #fb8500; }
        .issue.medium { border-left: 4px solid #ffd60a; }
        .issue.low { border-left: 4px solid #28a745; }
        .issue.info { border-left: 4px solid #0366d6; }
        .code { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 3px; padding: 10px; font-family: 'SFMono-Regular', Consolas, monospace; overflow-x: auto; }
        .location { color: #586069; font-size: 0.9em; }
        .confidence { background: #e1e4e8; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }
        h1, h2, h3 { color: #24292e; }
        .score { font-size: 1.5em; font-weight: bold; color: #28a745; }
    </style>
</head>
<body>""")
        
        # Header
        html_parts.append(f"""
<div class="header">
    <h1>Code Review Report</h1>
    <p><strong>ID:</strong> {review_result.id}</p>
    <p><strong>Status:</strong> {review_result.status.value}</p>
    <p><strong>Created:</strong> {review_result.created_at.isoformat()}</p>
</div>""")
        
        # Summary
        if review_result.summary:
            html_parts.append(f"""
<h2>Summary</h2>
<p>{review_result.summary}</p>""")
        
        # Metrics
        metrics = review_result.metrics
        score = metrics.calculate_score()
        html_parts.append(f"""
<h2>Metrics</h2>
<div class="metrics">
    <div class="metric-card">
        <h3>Files</h3>
        <p>{metrics.files_reviewed} reviewed</p>
    </div>
    <div class="metric-card">
        <h3>Changes</h3>
        <p>+{metrics.lines_added} -{metrics.lines_deleted}</p>
    </div>
    <div class="metric-card">
        <h3>Issues</h3>
        <p>{metrics.total_issues} total</p>
    </div>
    <div class="metric-card">
        <h3>Quality Score</h3>
        <p class="score">{score:.1f}/100</p>
    </div>
</div>""")
        
        # Issues
        if review_result.issues:
            html_parts.append("<h2>Issues</h2>")
            
            for issue in review_result.issues:
                html_parts.append(f"""
<div class="issue {issue.severity.value}">
    <h3>{issue.title}</h3>
    <p class="location">📁 {issue.location.file_path}:{issue.location.line_range}</p>
    <p>🏷️ {issue.category.value} | <span class="confidence">{issue.confidence:.1%} confidence</span></p>
    <p>{issue.description}</p>""")
                
                if issue.code_snippet:
                    html_parts.append(f"""
    <h4>Code:</h4>
    <div class="code">{self._escape_html(issue.code_snippet)}</div>""")
                
                if issue.suggested_fix:
                    html_parts.append(f"""
    <h4>Suggested Fix:</h4>
    <div class="code">{self._escape_html(issue.suggested_fix)}</div>""")
                
                html_parts.append("</div>")
        
        # Recommendations
        if review_result.recommendations:
            html_parts.append("<h2>Recommendations</h2>")
            html_parts.append("<ul>")
            for rec in review_result.recommendations:
                html_parts.append(f"<li>{rec}</li>")
            html_parts.append("</ul>")
        
        # Footer
        html_parts.append(f"""
<hr>
<p><em>Generated by Code Review CLI at {datetime.now().isoformat()}</em></p>
</body>
</html>""")
        
        return "\n".join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
    
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
    
    def save_to_file(
        self,
        content: str,
        filename: Optional[str] = None,
        format_type: Optional[str] = None,
    ) -> Path:
        """
        Save formatted output to file.
        
        Args:
            content: Content to save
            filename: Custom filename (optional)
            format_type: Output format for extension
            
        Returns:
            Path to saved file
        """
        if not self.config.save_to_file:
            raise ValueError("File saving is disabled in configuration")
        
        # Create output directory
        output_dir = Path(self.config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            format_ext = format_type or self.config.default_format
            ext_map = {
                "json": "json",
                "markdown": "md",
                "html": "html",
                "rich": "txt",
            }
            ext = ext_map.get(format_ext, "txt")
            filename = f"review_{timestamp}.{ext}"
        
        file_path = output_dir / filename
        
        # Write content
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Review saved to: {file_path}")
        
        return file_path
    
    def get_summary_stats(self, review_result: ReviewResult) -> Dict[str, Any]:
        """
        Get summary statistics for the review.
        
        Args:
            review_result: Review result
            
        Returns:
            Summary statistics dictionary
        """
        metrics = review_result.metrics
        
        return {
            "id": review_result.id,
            "status": review_result.status.value,
            "files_reviewed": metrics.files_reviewed,
            "total_issues": metrics.total_issues,
            "blocking_issues": metrics.blocking_issues,
            "quality_score": metrics.calculate_score(),
            "lines_changed": metrics.total_changes,
            "approved": review_result.is_approved(),
            "duration": metrics.review_duration,
            "cost_estimate": metrics.cost_estimate,
        } 