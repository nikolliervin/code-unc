# Configuration Guide

Learn how to configure UNC for your needs.

## Configuration File Location

UNC looks for configuration in the following order:
1. `--config` command line argument
2. `~/.config/unc/config.yaml`
3. `./unc.yaml`
4. Default configuration

## Default Configuration

The default configuration includes:

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
  
  # Mistral Settings
  mistral_api_key: null  # Set via MISTRAL_API_KEY environment variable
  
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
    - "*.log"
    - "*.tmp"
    - "node_modules/*"
    - ".git/*"
    # ... more patterns

# Cache Configuration  
cache:
  enabled: true
  git_diff_ttl: 3600      # 1 hour
  ai_response_ttl: 86400  # 24 hours
  max_size_mb: 100        # Maximum cache size

# History Configuration
history:
  enabled: false          # Enable/disable review history tracking (disabled by default)
  max_entries: 1000       # Maximum number of reviews to keep
  retention_days: 30      # Days to keep history entries
  storage_path: null      # Custom storage path (defaults to ~/.config/unc/history)
```

## Configuration Commands

### View Configuration

```bash
# Show current configuration
unc config show

# Show raw YAML configuration
unc config raw
```

### Set Configuration Values

```bash
# Set AI provider
unc config set ai.provider openai

# Set API key
unc config set ai.openai_api_key "your-api-key"

# Set model
unc config set ai.model "gpt-4"

# Set output format
unc config set output.format json

# Enable history tracking
unc config set history.enabled true

# Set history retention (optional)
unc config set history.retention_days 60
```

### Validate Configuration

```bash
# Validate current configuration
unc config validate
```

## Environment Variables

You can also configure UNC using environment variables:

```bash
# AI Provider API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export MISTRAL_API_KEY="your-mistral-key"
export GEMINI_API_KEY="your-gemini-key"

# Configuration
export CODE_UNC_CONFIG_PATH="./custom-config.yaml"
export CODE_UNC_VERBOSE="true"
```

## Configuration Examples

### OpenAI Configuration
```yaml
ai:
  provider: "openai"
  model: "gpt-4-turbo"
  temperature: 0.1
  max_tokens: 4000
  openai_api_key: "sk-..."  # or use environment variable
```

### Anthropic Configuration
```yaml
ai:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  temperature: 0.1
  max_tokens: 4000
  anthropic_api_key: "sk-ant-..."  # or use environment variable
```

### Mistral Configuration
```yaml
ai:
  provider: "mistral"
  model: "mistral-large-latest"
  temperature: 0.1
  max_tokens: 4000
  mistral_api_key: "your-api-key"  # or use environment variable
```

### Ollama Configuration
```yaml
ai:
  provider: "ollama"
  model: "codellama:7b"
  temperature: 0.1
  max_tokens: 4000
  ollama_base_url: "http://localhost:11434"
  ollama_model: "codellama:7b"
```

### History Configuration Examples

#### Enable History Tracking
```yaml
history:
  enabled: true           # Turn on history tracking
  max_entries: 1000       # Keep last 1000 reviews
  retention_days: 30      # Keep for 30 days
```

#### Custom History Storage
```yaml
history:
  enabled: true
  max_entries: 500
  retention_days: 14
  storage_path: "/custom/path/to/history"  # Custom location
```

#### Disable History (Default)
```yaml
history:
  enabled: false          # No history tracking
```

## Next Steps

- **[AI Providers Guide](ai-providers.md)** - Detailed AI provider setup
- **[Commands Reference](commands.md)** - All configuration commands
- **[Examples](examples.md)** - Configuration examples 