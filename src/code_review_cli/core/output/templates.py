"""Template management for output formatting."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, BaseLoader, Template

from ...models.review import ReviewResult


logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages output templates for various formats."""
    
    def __init__(self):
        """Initialize template manager with built-in templates."""
        self.templates: Dict[str, str] = {}
        self.jinja_env = Environment(loader=BaseLoader())
        self._load_builtin_templates()
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        # Simple text summary template
        self.templates["summary"] = """
Review Summary for {{ review.id }}
=================================
Status: {{ review.status.value }}
Files: {{ review.metrics.files_reviewed }}
Issues: {{ review.metrics.total_issues }} (Critical: {{ review.metrics.critical_issues }}, High: {{ review.metrics.high_issues }})
Score: {{ "%.1f"|format(review.metrics.calculate_score()) }}/100
Approved: {{ "Yes" if review.is_approved() else "No" }}
        """.strip()
        
        # Slack/Teams notification template
        self.templates["slack"] = """
{
    "text": "Code Review Complete",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔍 Code Review Report"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Repository:* {{ review.diff.repository or 'Unknown' }}"
                },
                {
                    "type": "mrkdwn", 
                    "text": "*Branch:* {{ review.diff.source_branch }} → {{ review.diff.target_branch }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Files:* {{ review.metrics.files_reviewed }}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Issues:* {{ review.metrics.total_issues }}"
                }
            ]
        },
        {% if review.metrics.total_issues > 0 %}
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Issue Breakdown:*\\n🚨 Critical: {{ review.metrics.critical_issues }}\\n⚠️ High: {{ review.metrics.high_issues }}\\n⚡ Medium: {{ review.metrics.medium_issues }}\\n💡 Low: {{ review.metrics.low_issues }}\\nℹ️ Info: {{ review.metrics.info_issues }}"
            }
        },
        {% endif %}
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Quality Score:* {{ "%.1f"|format(review.metrics.calculate_score()) }}/100"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "{% if review.is_approved() %}✅ *APPROVED* - Ready to merge!{% else %}❌ *NEEDS ATTENTION* - {{ review.get_blocking_issues()|length }} blocking issue(s){% endif %}"
            }
        }
    ]
}
        """.strip()
        
        # GitHub PR comment template  
        self.templates["github_comment"] = """
## 🔍 Code Review Report

**Review ID:** `{{ review.id }}`  
**Status:** {{ review.status.value }}  
**Quality Score:** {{ "%.1f"|format(review.metrics.calculate_score()) }}/100

### 📊 Summary
- **Files Reviewed:** {{ review.metrics.files_reviewed }}
- **Lines Changed:** +{{ review.metrics.lines_added }} -{{ review.metrics.lines_deleted }}
- **Total Issues:** {{ review.metrics.total_issues }}

{% if review.metrics.total_issues > 0 %}
### 🐛 Issues Found
| Severity | Count |
|----------|-------|
{% if review.metrics.critical_issues > 0 %}| 🚨 Critical | {{ review.metrics.critical_issues }} |
{% endif %}
{% if review.metrics.high_issues > 0 %}| ⚠️ High | {{ review.metrics.high_issues }} |
{% endif %}
{% if review.metrics.medium_issues > 0 %}| ⚡ Medium | {{ review.metrics.medium_issues }} |
{% endif %}
{% if review.metrics.low_issues > 0 %}| 💡 Low | {{ review.metrics.low_issues }} |
{% endif %}
{% if review.metrics.info_issues > 0 %}| ℹ️ Info | {{ review.metrics.info_issues }} |
{% endif %}

{% for issue in review.issues[:5] %}
#### {{ loop.index }}. {{ issue.title }}
**File:** `{{ issue.location.file_path }}:{{ issue.location.line_range }}`  
**Severity:** {{ issue.severity.value.title() }} | **Category:** {{ issue.category.value }}

{{ issue.description }}

{% if issue.code_snippet %}
<details>
<summary>Show Code</summary>

```{{ issue.location.file_path.split('.')[-1] if '.' in issue.location.file_path else 'text' }}
{{ issue.code_snippet }}
```
</details>
{% endif %}

{% if issue.suggested_fix %}
<details>
<summary>Suggested Fix</summary>

```{{ issue.location.file_path.split('.')[-1] if '.' in issue.location.file_path else 'text' }}
{{ issue.suggested_fix }}
```
</details>
{% endif %}

---
{% endfor %}

{% if review.issues|length > 5 %}
*... and {{ review.issues|length - 5 }} more issues. See full report for details.*
{% endif %}
{% endif %}

### 🎯 Recommendations
{% for rec in review.recommendations %}
- {{ rec }}
{% endfor %}

### ✅ Approval Status
{% if review.is_approved() %}
**✅ APPROVED** - No blocking issues found. Ready to merge!
{% else %}
**❌ NEEDS ATTENTION** - {{ review.get_blocking_issues()|length }} blocking issue(s) require fixes before merging.
{% endif %}

---
*Generated by Code Review CLI*
        """.strip()
        
        # Email template
        self.templates["email"] = """
Subject: Code Review Complete - {{ review.diff.repository }} ({{ review.diff.source_branch }} → {{ review.diff.target_branch }})

Code Review Report
==================

Review ID: {{ review.id }}
Repository: {{ review.diff.repository or 'Unknown' }}
Branch: {{ review.diff.source_branch }} → {{ review.diff.target_branch }}
Status: {{ review.status.value }}
Generated: {{ review.created_at.strftime('%Y-%m-%d %H:%M:%S') }}

Summary
-------
{% if review.summary %}
{{ review.summary }}
{% endif %}

Metrics
-------
Files Reviewed: {{ review.metrics.files_reviewed }}
Lines Added: {{ review.metrics.lines_added }}
Lines Deleted: {{ review.metrics.lines_deleted }}
Total Issues: {{ review.metrics.total_issues }}
Quality Score: {{ "%.1f"|format(review.metrics.calculate_score()) }}/100

{% if review.metrics.total_issues > 0 %}
Issue Breakdown:
- Critical: {{ review.metrics.critical_issues }}
- High: {{ review.metrics.high_issues }}
- Medium: {{ review.metrics.medium_issues }}
- Low: {{ review.metrics.low_issues }}
- Info: {{ review.metrics.info_issues }}
{% endif %}

{% if review.issues %}
Issues Found
------------
{% for issue in review.issues %}
{{ loop.index }}. {{ issue.title }}
   File: {{ issue.location.file_path }}:{{ issue.location.line_range }}
   Severity: {{ issue.severity.value.title() }}
   Category: {{ issue.category.value }}
   
   {{ issue.description }}
   
{% if issue.code_snippet %}
   Code:
   {{ issue.code_snippet | indent(3) }}
{% endif %}
{% if issue.suggested_fix %}
   
   Suggested Fix:
   {{ issue.suggested_fix | indent(3) }}
{% endif %}

{% endfor %}
{% endif %}

{% if review.recommendations %}
Recommendations
---------------
{% for rec in review.recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}
{% endif %}

Approval Status
---------------
{% if review.is_approved() %}
✅ APPROVED - No blocking issues found. Ready to merge!
{% else %}
❌ NEEDS ATTENTION - {{ review.get_blocking_issues()|length }} blocking issue(s) require fixes before merging.
{% endif %}

--
Generated by Code Review CLI
        """.strip()
    
    def render_template(
        self,
        template_name: str,
        review_result: ReviewResult,
        **kwargs
    ) -> str:
        """
        Render a template with review data.
        
        Args:
            template_name: Name of template to render
            review_result: Review result data
            **kwargs: Additional template variables
            
        Returns:
            Rendered template string
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template_str = self.templates[template_name]
        template = self.jinja_env.from_string(template_str)
        
        # Prepare template variables
        template_vars = {
            "review": review_result,
            **kwargs
        }
        
        try:
            return template.render(**template_vars)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise ValueError(f"Template rendering error: {e}")
    
    def add_template(self, name: str, template_str: str) -> None:
        """
        Add a custom template.
        
        Args:
            name: Template name
            template_str: Template string (Jinja2 format)
        """
        self.templates[name] = template_str
        logger.info(f"Added template: {name}")
    
    def load_template_from_file(self, name: str, file_path: Path) -> None:
        """
        Load template from file.
        
        Args:
            name: Template name
            file_path: Path to template file
        """
        try:
            template_str = file_path.read_text(encoding='utf-8')
            self.add_template(name, template_str)
        except Exception as e:
            logger.error(f"Failed to load template from {file_path}: {e}")
            raise ValueError(f"Template loading error: {e}")
    
    def list_templates(self) -> Dict[str, str]:
        """
        List all available templates.
        
        Returns:
            Dictionary mapping template names to descriptions
        """
        descriptions = {
            "summary": "Simple text summary",
            "slack": "Slack/Teams notification JSON",
            "github_comment": "GitHub PR comment markdown",
            "email": "Email notification text",
        }
        
        result = {}
        for name in self.templates.keys():
            result[name] = descriptions.get(name, "Custom template")
        
        return result
    
    def get_template_preview(self, template_name: str, max_lines: int = 10) -> str:
        """
        Get a preview of a template.
        
        Args:
            template_name: Template name
            max_lines: Maximum lines to show
            
        Returns:
            Template preview
        """
        if template_name not in self.templates:
            return "Template not found"
        
        template_str = self.templates[template_name]
        lines = template_str.split('\n')
        
        if len(lines) <= max_lines:
            return template_str
        
        preview_lines = lines[:max_lines]
        preview_lines.append(f"... ({len(lines) - max_lines} more lines)")
        
        return '\n'.join(preview_lines)
    
    def validate_template(self, template_str: str) -> bool:
        """
        Validate template syntax.
        
        Args:
            template_str: Template string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.jinja_env.from_string(template_str)
            return True
        except Exception as e:
            logger.warning(f"Template validation failed: {e}")
            return False 