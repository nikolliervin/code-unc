# AI Code Review GitHub Action Setup Guide

## Overview

This GitHub Action automatically runs AI-powered code reviews on pull requests using the UNC (Universal Code) tool. It provides intelligent feedback through inline comments on specific lines of code and generates comprehensive review summaries.

## Features

- **AI-Powered Analysis**: Uses advanced AI models to detect code issues
- **Inline Comments**: Posts feedback directly on problematic lines in the diff view
- **Comprehensive Summaries**: Generates detailed markdown reports with severity breakdown
- **Multi-Commit Support**: Automatically handles complex PR scenarios
- **Smart File Matching**: Accurately maps issues to the correct files
- **Professional Formatting**: Clean, organized output with severity indicators

## Quick Start

1. **Add the workflow file** to your repository at `.github/workflows/code-review.yml`
2. **Configure secrets** in your repository settings
3. **Create a pull request** to trigger the review

## Setup Instructions

### 1. Add the Workflow File

Create `.github/workflows/code-review.yml` in your repository with the following content:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  code-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install UNC
      run: pip install git+https://github.com/nikolliervin/code-unc.git
    
    - name: Initialize UNC config
      run: |
        mkdir -p ~/.config/unc
        cat > ~/.config/unc/config.yaml << 'EOF'
        ai:
          provider: "${{ secrets.AI_PROVIDER }}"
          model: "${{ secrets.AI_MODEL }}"
          temperature: 0.1
          max_tokens: 4000
          max_retries: 3
          retry_delay: 1.0
          timeout: 300
          gemini_api_key: "${{ secrets.GEMINI_API_KEY }}"
          openai_api_key: "${{ secrets.OPENAI_API_KEY }}"
        
        output:
          format: "json"
          show_progress: false
          show_metrics: true
          show_suggestions: true
          max_issues_display: 50
          color_enabled: false
        
        git:
          default_source: "HEAD"
          default_target: "main"
          max_diff_size: 1000000
          include_patterns: []
          exclude_patterns: ["*.log", "*.tmp", "node_modules/*", ".git/*"]
          binary_files: false
        
        cache:
          enabled: true
          ttl_hours: 24
          max_size_mb: 100
          cleanup_interval_hours: 168
        
        review:
          default_focus: []
          severity_threshold: "LOW"
          max_files_per_review: 100
          timeout_seconds: 300
        EOF
    
    - name: Prepare git
      run: |
        git config --global user.name "github-actions"
        git config --global user.email "github-actions@github.com"
        git branch -D pr-source 2>/dev/null || true
        git branch -D pr-target 2>/dev/null || true
        git branch pr-target ${{ github.event.pull_request.base.sha }}
        git branch pr-source ${{ github.event.pull_request.head.sha }}
        git checkout pr-source
    
    # ... [rest of the workflow content from your file]
```

### 2. Configure Repository Secrets

Navigate to your repository → **Settings** → **Secrets and variables** → **Actions** and add the following secrets:

#### Required Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AI_PROVIDER` | AI service provider | `gemini`, `openai`, `anthropic`, or `mistral` |
| `AI_MODEL` | Specific AI model to use | `gemini-1.5-pro`, `gpt-4`, `claude-3-sonnet`, `mistral-large-latest` |

#### Provider-Specific API Keys (Choose One)

**For Google Gemini:**
| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `GEMINI_API_KEY` | Google Gemini API key | [Get API Key](https://aistudio.google.com/app/apikey) |

**For OpenAI:**
| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `OPENAI_API_KEY` | OpenAI API key | [OpenAI Platform](https://platform.openai.com/api-keys) |

**For Anthropic:**
| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `ANTHROPIC_API_KEY` | Anthropic API key | [Anthropic Console](https://console.anthropic.com/) |

**For Mistral:**
| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `MISTRAL_API_KEY` | Mistral API key | [Mistral Platform](https://console.mistral.ai/) |

### 3. How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter the secret name and value
6. Click **Add secret**

#### Example Configuration

**For Google Gemini:**
```
AI_PROVIDER = gemini
AI_MODEL = gemini-1.5-pro
GEMINI_API_KEY = AIzaSyC...your-actual-api-key...
```

**For OpenAI:**
```
AI_PROVIDER = openai  
AI_MODEL = gpt-4
OPENAI_API_KEY = sk-proj-...your-actual-api-key...
```

**For Anthropic:**
```
AI_PROVIDER = anthropic
AI_MODEL = claude-3-sonnet-20240229
ANTHROPIC_API_KEY = sk-ant-...your-actual-api-key...
```

**For Mistral:**
```
AI_PROVIDER = mistral
AI_MODEL = mistral-large-latest
MISTRAL_API_KEY = ...your-actual-api-key...
```

## Usage

### Triggering Reviews

The action automatically triggers on:
- **New pull requests** (`opened`)
- **Pull request updates** (`synchronize`) 
- **Reopened pull requests** (`reopened`)

### What You'll See

#### 1. Inline Comments
The action posts comments directly on problematic lines:

```
🚨 CRITICAL: Hardcoded API secrets detected

This code contains hardcoded API keys which poses a severe security risk. 
Secrets should be stored in environment variables or a secure secrets manager.

Suggestion: Move these to environment variables
Category: security
Generated by UNC AI Code Review
```

#### 2. Summary Comment
A comprehensive markdown summary is posted to the PR:

```markdown
## AI Code Review Results

### Found 5 Issues

**Severity Breakdown:** 🚨 1 Critical • ⚠️ 2 High • 💡 2 Medium

### Issue Details

#### 🚨 CRITICAL: Production secrets exposed
**Location:** `src/config/database.js:15`
**Category:** security (95% confidence)

The database configuration contains hardcoded credentials...

### Review Statistics
- **Files Reviewed:** 3
- **Lines Added:** +142
- **Lines Deleted:** -28
```

## Configuration Options

### AI Provider Settings

You can customize the AI behavior by modifying the config in the workflow:

```yaml
ai:
  provider: "gemini"           # AI provider (gemini/openai/anthropic/mistral)
  model: "gemini-1.5-pro"     # Specific model
  temperature: 0.1            # Response randomness (0.0-1.0)
  max_tokens: 4000            # Maximum response length
  timeout: 300                # Request timeout in seconds
```

### Review Settings

```yaml
review:
  severity_threshold: "LOW"    # Minimum severity to report (LOW/MEDIUM/HIGH/CRITICAL)
  max_files_per_review: 100   # Maximum files to review per PR
  timeout_seconds: 300        # Review timeout
```

### File Filtering

```yaml
git:
  include_patterns: ["*.js", "*.ts", "*.py"]  # Only review these files
  exclude_patterns: [                         # Skip these files/patterns
    "*.log", 
    "*.tmp", 
    "node_modules/*", 
    ".git/*",
    "dist/*",
    "build/*"
  ]
```

## Advanced Configuration

### Custom Focus Areas

You can specify focus areas for more targeted reviews:

```yaml
review:
  default_focus: ["security", "performance", "bugs"]
```

Available focus areas:
- `security` - Security vulnerabilities and best practices
- `performance` - Performance optimizations and bottlenecks  
- `bugs` - Potential bugs and logical errors
- `maintainability` - Code organization and readability
- `testing` - Test coverage and quality

### Branch Configuration

Customize which branches trigger reviews:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main, develop]  # Only for PRs to these branches
```

## Troubleshooting

### Common Issues

#### 1. "No inline comments posted"
**Cause:** File paths don't match between UNC output and GitHub PR  
**Solution:** Check that file paths in your repository match the expected structure

#### 2. "API key not found"
**Cause:** Missing or incorrectly named secret  
**Solution:** Verify secret names match exactly (case-sensitive)

#### 3. "Rate limit exceeded"
**Cause:** Too many API requests to AI provider  
**Solution:** Reduce `max_files_per_review` or increase `retry_delay`

#### 4. "Permission denied"
**Cause:** Insufficient GitHub token permissions  
**Solution:** Ensure workflow has `pull-requests: write` permission

### Debug Mode

To enable detailed logging for troubleshooting, add this to your workflow:

```yaml
- name: Enable debug logging
  run: echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
```

### Viewing Logs

1. Go to the **Actions** tab in your repository
2. Click on the failed workflow run
3. Expand the "Run UNC and extract JSON" step
4. Look for error messages and debug information

## Best Practices

### 1. Repository Setup
- Test with a small PR first
- Review and adjust severity threshold based on your team's needs
- Customize excluded file patterns for your project structure

### 2. API Key Management
- Use repository secrets (never commit API keys)
- Rotate API keys regularly
- Use separate keys for different environments

### 3. Team Workflow
- Document the review process for your team
- Set expectations about automated vs manual reviews
- Use the action as a supplement to, not replacement for, human review

### 4. Cost Management
- Monitor AI provider usage and costs
- Adjust `max_files_per_review` for large repositories
- Consider using different models for different file types

## Example Configurations

### Minimal Setup (Gemini)
```yaml
# Repository Secrets:
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
GEMINI_API_KEY=your-api-key
```

### Production Setup (OpenAI)
```yaml
# Repository Secrets:
AI_PROVIDER=openai
AI_MODEL=gpt-4
OPENAI_API_KEY=your-api-key

# Workflow config adjustments:
temperature: 0.0              # More consistent results
max_files_per_review: 50      # Limit for large repos
severity_threshold: "MEDIUM"  # Reduce noise
```

### Security-Focused Setup
```yaml
# Focus on security issues only
review:
  default_focus: ["security"]
  severity_threshold: "HIGH"
  
# Exclude non-security relevant files
git:
  exclude_patterns: [
    "*.md", "*.txt", "*.json",
    "test/*", "tests/*", 
    "docs/*"
  ]
```

## Support

- **Issues:** [GitHub Issues](https://github.com/nikolliervin/code-unc/issues)
- **Documentation:** [UNC Documentation](https://github.com/nikolliervin/code-unc)
- **Discussions:** [GitHub Discussions](https://github.com/nikolliervin/code-unc/discussions)

## License

This workflow is provided as-is. Please review your AI provider's terms of service regarding automated code analysis. 