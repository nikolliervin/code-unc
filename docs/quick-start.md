# Quick Start Guide

Get up and running with UNC in minutes!

## Prerequisites

- UNC installed (see [Installation Guide](installation.md))
- Git repository with changes to review
- AI provider configured (see [AI Providers Guide](ai-providers.md))

## Quick Start Steps

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/nikolliervin/code-unc.git
cd code-unc

# Install in development mode
pip install -e .

# Add to PATH (if needed)
# Windows: Add Python Scripts directory to PATH
# macOS/Linux: export PATH="$HOME/.local/bin:$PATH"

# Verify installation
unc version
```

### 2. Initialize Configuration

```bash
# Interactive setup wizard
unc config init
```

This will guide you through:
- AI provider selection
- API key configuration
- Model selection
- Default settings

### 3. Run Your First Review

```bash
# Basic review (current branch vs main)
unc review run-review

# Review specific branches
unc review run-review --source feature-branch --target main

# Review with focus areas
unc review run-review --focus security --focus performance
```

## What's Next?

- **[Configuration Guide](configuration.md)** - Customize UNC settings
- **[Commands Reference](commands.md)** - Learn all available commands
- **[Examples](examples.md)** - See more usage examples
- **[AI Providers Guide](ai-providers.md)** - Configure different AI providers 