# Output Formats

UNC supports multiple output formats for different use cases.

## Available Formats

### Rich (Default)
- **Description**: Colorful, formatted terminal output
- **Use Case**: Interactive use, human reading
- **Command**: `unc review run-review`

### JSON
- **Description**: Machine-readable JSON output
- **Use Case**: Scripting, CI/CD integration
- **Command**: `unc review run-review --format json`

### Markdown
- **Description**: Markdown formatted output
- **Use Case**: Documentation, pull requests
- **Command**: `unc review run-review --format markdown`

### HTML
- **Description**: HTML formatted output
- **Use Case**: Web viewing, reports
- **Command**: `unc review run-review --format html`

## Format Examples

### Rich Output
```bash
unc review run-review
```
Shows colorful, interactive output with tables and progress bars.

### JSON Output
```bash
unc review run-review --format json
```
```json
{
  "review_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "feature-branch",
  "target": "main",
  "issues": [
    {
      "severity": "HIGH",
      "category": "security",
      "message": "Potential SQL injection vulnerability",
      "file": "src/database.py",
      "line": 42
    }
  ]
}
```

### Markdown Output
```bash
unc review run-review --format markdown > review.md
```
```markdown
# Code Review Report

**Review ID:** abc12345-def6-7890-ghij-klmnopqrstuv  
**Date:** 2024-01-15T10:30:00Z  
**Source:** feature-branch  
**Target:** main  

## Issues Found

### High Severity
- **Security Issue:** Potential SQL injection vulnerability in `src/database.py:42`
```

### HTML Output
```bash
unc review run-review --format html > review.html
```
Generates a complete HTML report with styling.

## Configuration

### Set Default Format
```bash
# Set default output format
unc config set output.format json
```

### Format Options
```yaml
output:
  format: "rich"  # Options: rich, json, markdown, html
  show_progress: true
  show_metrics: true
  show_suggestions: true
  max_issues_display: 50
  color_enabled: true
```

## Use Cases

### Interactive Development
```bash
# Use rich format for development
unc review run-review
```

### CI/CD Integration
```bash
# Use JSON for automation
unc review run-review --format json > review.json

# Process with jq
jq '.issues[] | select(.severity == "CRITICAL")' review.json
```

### Documentation
```bash
# Generate markdown for PRs
unc review run-review --format markdown > REVIEW.md
```

### Reports
```bash
# Generate HTML reports
unc review run-review --format html > report.html
```

## Next Steps

- **[Commands Reference](commands.md)** - Complete command reference
- **[Examples](examples.md)** - Output format examples
- **[Configuration Guide](configuration.md)** - Configure output settings 