# Commands Reference

Complete reference for all UNC commands.

## Main Commands

### `unc help`
Show comprehensive help with examples and command reference.

**Usage:**
```bash
unc help
```

### `unc version`
Show version and exit.

**Usage:**
```bash
unc version
```

## Review Commands

### `unc review run-review`
Run AI code review on git diff.

**Arguments:**
- `--source, -s TEXT`: Source branch/commit (default: HEAD)
- `--target, -t TEXT`: Target branch/commit (default: main)
- `--focus, -f [security|performance|style|general]`: Focus areas for review
- `--include, -i TEXT`: Include file patterns
- `--exclude, -e TEXT`: Exclude file patterns
- `--format, -o [rich|json|markdown|html]`: Output format
- `--verbose, -V`: Enable verbose output
- `--config, -c TEXT`: Path to configuration file

**Usage Examples:**
```bash
# Basic review
unc review run-review

# Review specific branches
unc review run-review --source feature-branch --target main

# Review with focus areas
unc review run-review --focus security --focus performance

# Review specific files
unc review run-review --include "*.py" --exclude "tests/*"

# JSON output
unc review run-review --format json

# Verbose output
unc review run-review --verbose
```

### `unc review list`
List recent reviews.

**Arguments:**
- `--limit, -l INTEGER`: Number of reviews to show (default: 10)
- `--format, -f [rich|json|markdown]`: Output format
- `--verbose, -V`: Enable verbose output

**Usage Examples:**
```bash
# List recent reviews
unc review list

# List with limit
unc review list --limit 5

# JSON format
unc review list --format json
```

### `unc review show`
Display detailed information about a specific review.

**Arguments:**
- `review_id TEXT`: Review ID to display (required)

**Usage Examples:**
```bash
# Show specific review
unc review show abc12345-def6-7890-ghij-klmnopqrstuv

# Show with review ID from list command
unc review show $(unc review list --format json | jq -r '.[0].id')
```

## Configuration Commands

### `unc config init`
Initialize configuration with interactive setup wizard.

**Features:**
- Interactive AI provider selection
- API key configuration (with secure input)
- Model selection based on provider
- Default settings configuration
- Configuration file creation

**Usage Examples:**
```bash
# Interactive setup
unc config init
```

### `unc config show`
Display current configuration settings.

**Usage Examples:**
```bash
# Show current configuration
unc config show
```

### `unc config raw`
Show raw YAML configuration.

**Usage Examples:**
```bash
# Show raw configuration
unc config raw
```

### `unc config set`
Set configuration value.

**Arguments:**
- `key TEXT`: Configuration key (e.g., ai.provider)
- `value TEXT`: Configuration value

**Usage Examples:**
```bash
# Set AI provider
unc config set ai.provider openai

# Set API key
unc config set ai.openai_api_key "your-api-key"

# Set model
unc config set ai.model "gpt-4"

# Set output format
unc config set output.format json
```

### `unc config validate`
Validate current configuration.

**Usage Examples:**
```bash
# Validate configuration
unc config validate
```

## History Commands

### `unc history list`
List review history.

**Arguments:**
- `--limit, -l INTEGER`: Number of reviews to show (default: 10)
- `--format, -f [rich|json|markdown]`: Output format
- `--verbose, -V`: Enable verbose output

**Usage Examples:**
```bash
# List review history
unc history list

# List with limit
unc history list --limit 5

# JSON format
unc history list --format json
```

### `unc history show`
Show detailed review by ID.

**Arguments:**
- `review_id TEXT`: Review ID to display (required)

**Usage Examples:**
```bash
# Show specific review
unc history show abc12345-def6-7890-ghij-klmnopqrstuv
```

### `unc history clear`
Clear all review history and cached data.

**Arguments:**
- `--yes, -y`: Skip confirmation prompt

**Usage Examples:**
```bash
# Clear with confirmation
unc history clear

# Clear without confirmation
unc history clear --yes
unc history clear -y
```

## Global Options

All commands support these global options:

- `--help`: Show help for the command
- `--verbose, -V`: Enable verbose output
- `--config, -c TEXT`: Path to configuration file

## Environment Variables

You can also configure UNC using environment variables:

```bash
# AI Provider API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"

# Configuration
export CODE_UNC_CONFIG_PATH="./custom-config.yaml"
export CODE_UNC_VERBOSE="true"
```

## Next Steps

- **[Examples](examples.md)** - Common usage examples
- **[AI Providers Guide](ai-providers.md)** - AI provider setup
- **[Configuration Guide](configuration.md)** - Configuration details 