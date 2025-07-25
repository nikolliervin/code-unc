# Quick Setup: AI Code Review GitHub Action

## Get Started in 5 Minutes

### Step 1: Copy the Workflow File
Copy [`.github/workflows/code-review.yml`](.github/workflows/code-review.yml) to your repository.

### Step 2: Add Secrets
Go to **Repository Settings** → **Secrets and variables** → **Actions** → **New repository secret**

#### For Google Gemini (Recommended - Free tier available):
```
AI_PROVIDER = gemini
AI_MODEL = gemini-1.5-pro  
GEMINI_API_KEY = [Get from https://aistudio.google.com/app/apikey]
```

#### For OpenAI:
```
AI_PROVIDER = openai
AI_MODEL = gpt-4
OPENAI_API_KEY = [Get from https://platform.openai.com/api-keys]
```

### Step 3: Create a Pull Request
The action will automatically run and post review comments!

## What You'll Get

- **Inline comments** on problematic code lines
- **Professional summary** with severity breakdown  
- **Smart file matching** and line detection
- **Multiple AI provider support**

## Common Configurations

### Reduce Noise (Recommended for Production):
```yaml
# In the workflow file, change:
severity_threshold: "MEDIUM"  # Only show MEDIUM+ issues
max_files_per_review: 50      # Limit for large repos
```

### Security Focus Only:
```yaml
# In the workflow file, add:
default_focus: ["security"]
severity_threshold: "HIGH"
```

### Exclude Common Files:
```yaml
# In the workflow file, add to exclude_patterns:
exclude_patterns: [
  "*.log", "*.tmp", "node_modules/*", ".git/*",
  "dist/*", "build/*", "coverage/*", 
  "*.test.js", "*.spec.ts"
]
```

## Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| No comments posted | Check file paths match your repo structure |
| API errors | Verify secret names are exactly: `AI_PROVIDER`, `AI_MODEL`, `GEMINI_API_KEY` |
| Permission denied | Ensure workflow has `pull-requests: write` permission |
| Too many issues | Increase `severity_threshold` to "MEDIUM" or "HIGH" |

## Full Documentation
See [docs/github-action-setup.md](docs/github-action-setup.md) for complete configuration options.

---
**Ready to use?** Just copy the workflow file and add your API key! 