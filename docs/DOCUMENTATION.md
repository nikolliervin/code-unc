# UNC Documentation

AI-powered code review tool using git diff and various AI providers (OpenAI, Anthropic, Mistral, Gemini, Ollama).

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Commands Reference](#commands-reference)
- [AI Providers](#ai-providers)
- [Focus Areas](#focus-areas)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- Git repository
- AI provider API key (depending on your choice)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/nikolliervin/code-unc.git
cd code-unc

# Install in development mode
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Adding to PATH

After installation, you may need to add the `unc` command to your system PATH to use it from anywhere in the terminal.

#### Windows

**Option 1: Using Python Scripts Directory**
```bash
# Find your Python Scripts directory
python -c "import sys; print(sys.executable.replace('python.exe', 'Scripts'))"

# Add to PATH (replace with your actual path)
# Example: C:\Users\YourUsername\AppData\Local\Programs\Python\Python39\Scripts
```

**Option 2: Using pip show**
```bash
# Find where pip installed the package
pip show code-review-cli

# Look for "Location" field and add the Scripts directory to PATH
```

**Option 3: Manual PATH Addition**
1. Open System Properties → Advanced → Environment Variables
2. Edit the "Path" variable
3. Add the Python Scripts directory path
4. Restart your terminal

#### macOS/Linux

**Option 1: Using pip user installation**
```bash
# Install with --user flag to install in user directory
pip install -e . --user

# The binary will be in ~/.local/bin
# Add to PATH in your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Option 2: Using virtual environment**
```bash
# Create and activate virtual environment
python -m venv unc-env
source unc-env/bin/activate  # On Windows: unc-env\Scripts\activate

# Install in virtual environment
pip install -e .

# The unc command will be available when virtual environment is activated
```

**Option 3: Using system-wide installation**
```bash
# Install system-wide (may require sudo)
sudo pip install -e .

# The unc command should be available globally
```

#### Verify Installation

After adding to PATH, verify the installation:

```bash
# Check if unc is available
unc version

# Or check the help
unc help
```

If you get a "command not found" error, restart your terminal or reload your shell profile.

## Quick Start

1. **Clone and Install**
   ```bash
   # Clone the repository
   git clone https://github.com/nikolliervin/code-unc.git
   cd code-unc
   
   # Install in development mode
   pip install -e .
   
   # Add to PATH (if needed)
   # Windows: Add Python Scripts directory to PATH
   # macOS/Linux: export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Initialize Configuration**
   ```bash
   unc config init
   ```

3. **Run Your First Review**
   ```bash
   unc review run-review --source feature-branch --target main
   ```

## Configuration

### Configuration File Location

The tool looks for configuration in the following order:
1. `--config` command line argument
2. `~/.config/unc/config.yaml`
3. `./unc.yaml`
4. Default configuration

### Default Configuration

The default configuration file (`configs/default.yaml`) includes:

```yaml
# AI Provider Configuration
ai:
  provider: "ollama"  # Options: openai, anthropic, mistral, gemini, ollama
  model: "tinyllama"  # Model name - provider specific
  temperature: 0.1    # 0.0 = deterministic, 1.0 = creative
  max_tokens: 4000    # Maximum tokens to generate
  
  # OpenAI Settings
  openai_api_key: null  # Set via OPENAI_API_KEY environment variable
  openai_base_url: null # Optional custom base URL
  
  # Anthropic Settings
  anthropic_api_key: null  # Set via ANTHROPIC_API_KEY environment variable
  
  # Google Gemini Settings
  gemini_api_key: null  # Set via GEMINI_API_KEY environment variable
  gemini_base_url: null # Optional custom base URL
  
  # Ollama Settings
  ollama_base_url: "http://localhost:11434"
  ollama_model: "tinyllama"
  
  # Retry Configuration
  max_retries: 3
  retry_delay: 1.0

# Review Configuration  
review:
  max_files: 50
  include_patterns: []
  focus_areas:
    - "general"
    - "security" 
    - "performance"
    - "style"

# Output Configuration
output:
  format: "rich"  # Options: rich, json, markdown, html
  show_progress: true
  show_metrics: true
  show_suggestions: true
  max_issues_display: 50
  console_width: null  # Auto-detect if null
  color_enabled: true

# Git Configuration
git:
  ignore_whitespace: false
  ignore_binary: true
  max_diff_size: 1000000  # 1MB limit
  exclude_patterns:
    # Build artifacts and dependencies
    - "*.log"
    - "*.tmp"
    - "node_modules/*"
    - ".git/*"
    - "package-lock.json"
    - "yarn.lock"
    - "pnpm-lock.yaml"
    - "*.lock"
    
    # Binary and asset files
    - "*.exe"
    - "*.dll"
    - "*.so"
    - "*.dylib"
    - "*.bin"
    - "*.ico"
    - "*.svg"
    - "*.png"
    - "*.jpg"
    - "*.jpeg"
    - "*.gif"
    - "*.bmp"
    - "*.webp"
    - "*.mp3"
    - "*.mp4"
    - "*.avi"
    - "*.mov"
    - "*.wav"
    - "*.flac"
    
    # Configuration and script files
    - "*.bat"
    - "*.cmd"
    - "*.sh"
    - "*.ps1"
    - "*.yml"
    - "*.yaml"
    - "*.toml"
    - "*.ini"
    - "*.cfg"
    - "*.conf"
    - ".env*"
    - "*.env"
    
    # IDE and editor files
    - ".vscode/*"
    - ".idea/*"
    - "*.swp"
    - "*.swo"
    - "*~"
    - ".DS_Store"
    - "Thumbs.db"
    
    # Documentation
    - "*.md"
    - "*.txt"
    - "*.pdf"
    - "*.doc"
    - "*.docx"
    
    # Archive files
    - "*.zip"
    - "*.tar"
    - "*.gz"
    - "*.rar"
    - "*.7z"
  
# Cache Configuration  
cache:
  enabled: true
  git_diff_ttl: 3600      # 1 hour
  ai_response_ttl: 86400  # 24 hours
  max_size_mb: 100        # Maximum cache size
```

## Commands Reference

This section provides a comprehensive reference for all available commands in unc, including detailed options, examples, and configuration adjustments.

### Main Commands

#### `unc --help`
Display help information for the main command or any subcommand.

```bash
unc --help                    # Main help
unc review --help             # Review commands help
unc config --help             # Config commands help
unc history --help            # History commands help
```

#### `unc version`
Display the current version of unc.

```bash
unc version
# Output: unc version 0.1.0
```

#### `unc --verbose` / `-V`
Enable verbose output for debugging and detailed information.

```bash
unc --verbose review run-review
unc -V config validate
```

#### `unc --config` / `-c`
Specify a custom configuration file path.

```bash
unc --config ./my-config.yaml review run-review
unc -c ~/.config/unc/production.yaml config show
```

### Review Commands

#### `unc review run-review`

Run AI-powered code review on git diff between branches or commits.

**Command Options:**
- `--target, -t TEXT`: Target branch/commit (default: "main")
- `--source, -s TEXT`: Source branch/commit (default: "HEAD")
- `--focus, -f TEXT`: Focus areas (security, performance, style, general) - can be specified multiple times
- `--include, -i TEXT`: File patterns to include - can be specified multiple times
- `--exclude, -e TEXT`: File patterns to exclude - can be specified multiple times
- `--output, -o TEXT`: Output format (rich, json, markdown) (default: "rich")
- `--max-files INTEGER`: Maximum files to review (default: 100)
- `--save TEXT`: Save output to file
- `--config TEXT`: Path to config file
- `--verbose, -v`: Verbose output

**Configuration Adjustments:**
```yaml
# In your config file, you can set defaults:
review:
  max_files: 50                    # Default max files per review
  focus_areas: ["security"]        # Default focus areas
  severity_threshold: "MEDIUM"     # Minimum severity to report
  timeout_seconds: 300             # Review timeout

git:
  exclude_patterns:                # Global exclude patterns
    - "*.test.py"
    - "node_modules/*"
    - "*.log"
```

**Usage Examples:**

**Basic Review:**
```bash
# Review current branch against main
unc review run-review

# Review specific branches
unc review run-review --source feature-auth --target main

# Review specific commits
unc review run-review --source abc1234 --target def5678
```

**Focused Reviews:**
```bash
# Security-focused review
unc review run-review --focus security

# Performance-focused review
unc review run-review --focus performance

# Multiple focus areas
unc review run-review --focus security --focus performance

# Style and maintainability
unc review run-review --focus style
```

**File Filtering:**
```bash
# Include only Python files
unc review run-review --include "*.py"

# Include multiple file types
unc review run-review --include "*.py" --include "*.js" --include "*.ts"

# Exclude test files
unc review run-review --exclude "*.test.py" --exclude "*_test.py"

# Exclude directories
unc review run-review --exclude "node_modules/*" --exclude "venv/*"

# Combine include and exclude
unc review run-review --include "*.py" --exclude "tests/*"
```

**Output Options:**
```bash
# Rich console output (default)
unc review run-review --output rich

# JSON output for programmatic processing
unc review run-review --output json

# Markdown output for documentation
unc review run-review --output markdown

# Save to file
unc review run-review --save review-report.json
unc review run-review --save review-report.md
```

**Advanced Usage:**
```bash
# Limit files and use custom config
unc review run-review --max-files 25 --config ./custom.yaml

# Verbose output for debugging
unc review run-review --verbose

# Complete example with all options
unc review run-review \
  --source feature-branch \
  --target main \
  --focus security \
  --focus performance \
  --include "*.py" \
  --exclude "tests/*" \
  --exclude "*.test.py" \
  --output json \
  --save security-review.json \
  --max-files 50 \
  --verbose
```

#### `unc review list`

List recent reviews with summary information.

**Command Options:**
- `--limit, -l INTEGER`: Number of reviews to show (default: 10)
- `--format, -f TEXT`: Output format (table, json) (default: "table")

**Usage Examples:**
```bash
# List last 10 reviews
unc review list

# List last 5 reviews
unc review list --limit 5

# JSON output
unc review list --format json

# List with custom limit
unc review list -l 20 -f json
```

#### `unc review show`

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

#### `unc review clear`

Clear all review history and cached data.

**Usage Examples:**
```bash
# Clear with confirmation prompt
unc review clear

# Clear without confirmation
unc review clear --yes
```

### Help Commands

#### `unc help`

Show comprehensive help with examples and command reference.

**Features:**
- Quick start guide
- Complete command reference
- Usage examples for all commands
- Tips and best practices

**Usage Examples:**
```bash
# Show comprehensive help
unc help

# The help includes:
# - Quick start guide
# - Main commands overview
# - Review commands with examples
# - Configuration commands with examples
# - History commands with examples
# - Common usage examples
# - Tips and best practices
```

### Configuration Commands

#### `unc config init`

Initialize configuration with interactive setup wizard.

**Features:**
- Interactive AI provider selection
- API key configuration (with secure input)
- Model selection based on provider
- Default settings configuration
- Configuration file creation

**Supported Providers:**
- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Anthropic**: Claude-3-opus, Claude-3-sonnet
- **Google Gemini**: Gemini-2.5-flash, Gemini-2.5-pro, Gemini-1.5-pro
- **Ollama**: Any local model (codellama, tinyllama, etc.)

**Usage Examples:**
```bash
# Interactive setup
unc config init

# The wizard will guide you through:
# 1. AI provider selection
# 2. API key entry (hidden input)
# 3. Model selection
# 4. Default settings
```

**Configuration File Created:**
```yaml
# ~/.config/unc/config.yaml
ai:
  provider: "openai"
  model: "gpt-4-turbo"
  temperature: 0.1
  max_tokens: 4000
  openai_api_key: "sk-..."  # Your API key

output:
  format: "rich"
  show_progress: true
  show_metrics: true
  color_enabled: true

git:
  exclude_patterns:
    - "*.log"
    - "node_modules/*"
    - ".git/*"

cache:
  enabled: true
  ttl_hours: 24
  max_size_mb: 100
```

#### `unc config show`

Display current configuration settings.

**Displays:**
- AI provider and model settings
- API key status (masked for security)
- Git configuration
- Output settings
- Cache settings
- File patterns and exclusions

**Usage Examples:**
```bash
# Show all configuration
unc config show

# Show with custom config file
unc config show --config ./custom.yaml
```

**Sample Output:**
```
Current Configuration

┌─────────────────────┬─────────────────────────────────────┐
│ Setting             │ Value                               │
├─────────────────────┼─────────────────────────────────────┤
│ AI Provider         │ openai                              │
│ Model               │ gpt-4-turbo                         │
│ Temperature         │ 0.1                                 │
│ Max Tokens          │ 4000                                │
│ OpenAI API Key      │ •••••••••••••••••••••••••••••••••• │
│ Output Format       │ rich                                │
│ Show Progress       │ Yes                                 │
│ Cache Enabled       │ Yes                                 │
│ Cache TTL           │ 24 hours                            │
└─────────────────────┴─────────────────────────────────────┘

Config file: ~/.config/unc/config.yaml
```

#### `unc config set`

Set individual configuration values.

**Usage:**
```bash
unc config set <key> <value>
```

**Configuration Keys:**
```bash
# AI Configuration
unc config set ai.provider openai
unc config set ai.model gpt-4-turbo
unc config set ai.temperature 0.2
unc config set ai.max_tokens 8000

# Output Configuration
unc config set output.format json
unc config set output.show_progress false
unc config set output.color_enabled false

# Git Configuration
unc config set git.max_diff_size 2000000
unc config set git.ignore_binary true

# Cache Configuration
unc config set cache.enabled false
unc config set cache.ttl_hours 48
unc config set cache.max_size_mb 200

# Review Configuration
unc config set review.max_files 75
unc config set review.severity_threshold HIGH
unc config set review.timeout_seconds 600
```

**Usage Examples:**
```bash
# Change AI provider
unc config set ai.provider anthropic
unc config set ai.model claude-3-sonnet-20240229

# Adjust output settings
unc config set output.format markdown
unc config set output.show_metrics false

# Modify review settings
unc config set review.max_files 100
unc config set review.severity_threshold LOW

# Disable cache
unc config set cache.enabled false
```

#### `unc config validate`

Validate current configuration for errors and warnings.

**Checks Performed:**
- Required fields presence
- Valid provider/model combinations
- API key presence and format
- Configuration file syntax
- File path accessibility
- Network connectivity (optional)

**Usage Examples:**
```bash
# Validate current config
unc config validate

# Validate with custom config
unc config validate --config ./test-config.yaml

# Verbose validation
unc config validate --verbose
```

**Sample Output:**
```
Validating Configuration

✓ Configuration is valid!

Configuration Summary:
Provider: openai
Model: gpt-4-turbo
Config file: ~/.config/unc/config.yaml

Warnings:
  • Max tokens is very high (8000), may cause issues
  • Temperature is set to 0.2, consider 0.1 for more consistent results
```

### History Commands

#### `unc history list`

List review history with metadata and statistics.

**Command Options:**
- `--limit, -l INTEGER`: Number of reviews to show (default: 10)
- `--format, -f TEXT`: Output format (table, json) (default: "table")

**Usage Examples:**
```bash
# List recent reviews
unc history list

# List last 20 reviews
unc history list --limit 20

# JSON output for processing
unc history list --format json

# Custom limit and format
unc history list -l 5 -f json
```

**Sample Output:**
```
Review History (last 10)

┌─────────────────────┬──────────────┬──────────────┬───────┬────────┐
│ Date                │ Source       │ Target       │ Files │ Issues │
├─────────────────────┼──────────────┼──────────────┼───────┼────────┤
│ 2024-01-15 14:30   │ feature-auth │ main         │ 12    │ 3      │
│ 2024-01-15 10:15   │ bugfix-login │ main         │ 5     │ 1      │
│ 2024-01-14 16:45   │ feature-api  │ develop      │ 18    │ 7      │
└─────────────────────┴──────────────┴──────────────┴───────┴────────┘
```

#### `unc history show`

Display detailed information about a specific review.

**Arguments:**
- `review_id TEXT`: Review ID to display (required)

**Usage Examples:**
```bash
# Show specific review
unc history show abc12345-def6-7890-ghij-klmnopqrstuv

# Show with ID from list
unc history show $(unc history list --format json | jq -r '.[0].id')
```

**Sample Output:**
```
Review Details: abc12345-def6-7890-ghij-klmnopqrstuv

┌─────────────────────────────────────────────────────────────────────────────┐
│ Review Information                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ ID: abc12345-def6-7890-ghij-klmnopqrstuv                                   │
│ Date: 2024-01-15 14:30:00 UTC                                              │
│ Source: feature-auth                                                        │
│ Target: main                                                                │
│ Focus: SECURITY                                                             │
│ Status: COMPLETED                                                           │
│ AI Provider: openai                                                         │
│ AI Model: gpt-4-turbo                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Statistics                                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Files Reviewed: 12                                                          │
│ Lines Added: 150                                                            │
│ Lines Deleted: 25                                                           │
│ Critical Issues: 0                                                          │
│ High Issues: 1                                                              │
│ Medium Issues: 2                                                            │
│ Low Issues: 0                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### `unc history clear`

Clear all review history and cached data.

**Command Options:**
- `--yes, -y`: Skip confirmation prompt

**Usage Examples:**
```bash
# Clear with confirmation
unc history clear

# Clear without confirmation
unc history clear --yes
unc history clear -y
```

**Sample Output:**
```
Are you sure you want to clear all review history? [y/N]: y
Clearing review history...
✓ Review history cleared successfully!
```

### Command Line Options Reference

#### Global Options

All commands support these global options:

- `--help`: Show help for the command
- `version`: Show version and exit
- `--verbose, -V`: Enable verbose output
- `--config, -c TEXT`: Path to configuration file

#### Environment Variables

You can also configure the tool using environment variables:

```bash
# AI Provider API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"

# Configuration
export CODE_UNC_CONFIG_PATH="./custom-config.yaml"
export CODE_UNC_VERBOSE="true"

# Then run commands
unc review run-review
```

#### Configuration File Override

You can override configuration file location:

```bash
# Use specific config file
unc --config ./production.yaml review run-review

# Use config from different location
unc --config ~/.config/unc/prod-config.yaml config show
```

## AI Providers

### OpenAI

**Configuration:**
```yaml
ai:
  provider: "openai"
  model: "gpt-4-turbo"  # or "gpt-4", "gpt-3.5-turbo"
  openai_api_key: "your-api-key"  # or set OPENAI_API_KEY env var
  openai_base_url: null  # Optional custom base URL
```

**Environment Variables:**
```bash
export OPENAI_API_KEY="your-api-key"
```

**Supported Models:**
- `gpt-4-turbo` (recommended)
- `gpt-4`
- `gpt-3.5-turbo`

### Anthropic

**Configuration:**
```yaml
ai:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"  # or "claude-3-opus-20240229"
  anthropic_api_key: "your-api-key"  # or set ANTHROPIC_API_KEY env var
```

**Environment Variables:**
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

**Supported Models:**
- `claude-3-opus-20240229` (most capable)
- `claude-3-sonnet-20240229` (balanced)

### Google Gemini

**Configuration:**
```yaml
ai:
  provider: "gemini"
  model: "gemini-2.5-flash"  # or other Gemini models
  gemini_api_key: "your-api-key"  # or set GEMINI_API_KEY env var
  gemini_base_url: null  # Optional custom base URL
```

**Environment Variables:**
```bash
export GEMINI_API_KEY="your-api-key"
```

**Supported Models:**
- `gemini-2.5-flash` (fastest, most cost-effective)
- `gemini-2.5-pro` (most capable)
- `gemini-2.0-flash`
- `gemini-1.5-flash`
- `gemini-1.5-pro`
- `gemini-1.0-pro`

### Ollama (Local)

**Configuration:**
```yaml
ai:
  provider: "ollama"
  model: "codellama:7b"  # or any Ollama model
  ollama_base_url: "http://localhost:11434"
  ollama_model: "codellama:7b"
```

**Setup:**
1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull codellama:7b`
3. Start Ollama service

**Recommended Models:**
- `codellama:7b` (good balance)
- `codellama:13b` (more capable)
- `codellama:34b` (most capable)
- `tinyllama` (fastest)

## Focus Areas

### General Review

Default comprehensive review covering all aspects.

```bash
unc review run-review --focus general
```

### Security Review

Focused on security vulnerabilities and best practices.

**Checks:**
- OWASP Top 10 vulnerabilities
- Authentication and authorization issues
- Input validation and sanitization
- SQL injection and XSS prevention
- Secure coding practices
- Dependency vulnerabilities

```bash
unc review run-review --focus security
```

### Performance Review

Focused on performance optimization and efficiency.

**Checks:**
- Algorithmic complexity analysis
- Database query optimization
- Memory usage and leaks
- I/O operations efficiency
- Caching strategies
- Concurrency and parallelism
- Resource management

```bash
unc review run-review --focus performance
```

### Style Review

Focused on code style and maintainability.

**Checks:**
- Naming conventions
- Code formatting
- Documentation
- Type hints
- Import organization
- File structure
- Consistency

```bash
unc review run-review --focus style
```

## Output Formats

### Rich Console Output (Default)

Colorized, formatted output with progress indicators and tables.

```bash
unc review run-review --output rich
```

### JSON Output

Structured JSON data for programmatic processing.

```bash
unc review run-review --output json
```

**Output Structure:**
```json
{
  "id": "review-uuid",
  "status": "COMPLETED",
  "request": {
    "source_branch": "feature-branch",
    "target_branch": "main",
    "focus": "GENERAL"
  },
  "diff": {
    "files": [...]
  },
  "issues": [
    {
      "id": "issue-uuid",
      "title": "Issue title",
      "description": "Detailed description",
      "severity": "HIGH",
      "category": "SECURITY",
      "location": {
        "file_path": "src/file.py",
        "line_start": 42,
        "line_end": 45
      },
      "code_snippet": "problematic code",
      "suggested_fix": "improved code",
      "confidence": 0.95,
      "tags": ["security", "injection"],
      "references": ["https://owasp.org/..."]
    }
  ],
  "summary": "Found 3 issues: 1 high, 2 medium priority",
  "metrics": {
    "critical_issues": 0,
    "high_issues": 1,
    "medium_issues": 2,
    "low_issues": 0,
    "info_issues": 0,
    "files_reviewed": 5,
    "lines_added": 150,
    "lines_deleted": 25
  },
  "created_at": "2024-01-15T10:30:00Z",
  "ai_provider_used": "openai",
  "ai_model_used": "gpt-4-turbo"
}
```

### Markdown Output

Markdown formatted output for documentation.

```bash
unc review run-review --output markdown
```

## Examples

### Basic Usage

```bash
# Initialize configuration
unc config init

# Run review on current branch vs main
unc review run-review

# Review specific branches
unc review run-review --source feature-auth --target main

# Security-focused review
unc review run-review --focus security --source feature-auth --target main
```

### Advanced Usage

```bash
# Review only Python files with security focus
unc review run-review \
  --focus security \
  --include "*.py" \
  --exclude "tests/*" \
  --exclude "migrations/*"

# Performance review with custom output
unc review run-review \
  --focus performance \
  --output json \
  --save performance-review.json

# Review with multiple focus areas
unc review run-review \
  --focus security \
  --focus performance \
  --max-files 50
```

### Configuration Examples

**OpenAI Configuration:**
```yaml
ai:
  provider: "openai"
  model: "gpt-4-turbo"
  temperature: 0.1
  max_tokens: 4000
  openai_api_key: "sk-..."  # or use environment variable
```

**Anthropic Configuration:**
```yaml
ai:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  temperature: 0.1
  max_tokens: 4000
  anthropic_api_key: "sk-ant-..."  # or use environment variable
```

**Ollama Configuration:**
```yaml
ai:
  provider: "ollama"
  model: "codellama:7b"
  temperature: 0.1
  max_tokens: 4000
  ollama_base_url: "http://localhost:11434"
  ollama_model: "codellama:7b"
```

## Troubleshooting

### Common Issues

**1. Command Not Found**
```bash
# If you get "unc: command not found", add to PATH:

# Windows - Find Python Scripts directory:
python -c "import sys; print(sys.executable.replace('python.exe', 'Scripts'))"

# macOS/Linux - Add to shell profile:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or install with --user flag:
pip install -e . --user
```

**2. Configuration Not Found**
```bash
# Initialize configuration
unc config init
```

**3. API Key Issues**
```bash
# Check configuration
unc config show

# Validate configuration
unc config validate
```

**3. Git Repository Issues**
```bash
# Ensure you're in a git repository
git status

# Check if branches exist
git branch -a
```

**4. No Files to Review**
```bash
# Check what files are being excluded
unc review run-review --verbose

# Include more file types
unc review run-review --include "*.py" --include "*.js"
```

**5. AI Provider Connection Issues**

**OpenAI:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test with curl
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Anthropic:**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test with curl
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/models
```

**Ollama:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Debug Mode

Enable verbose output for debugging:

```bash
unc review run-review --verbose
```

### Cache Management

Clear cache if you encounter issues:

```bash
# Clear review history
unc history clear --yes

# Or manually delete cache directory
rm -rf ~/.cache/unc/
```

### Environment Variables

Set these environment variables for API keys:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google Gemini
export GEMINI_API_KEY="your-gemini-api-key"
```

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/nikolliervin/code-unc.git
cd code-unc

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/
```



## License

MIT License - see LICENSE file for details. 
