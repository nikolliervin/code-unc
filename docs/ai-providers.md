# AI Providers Guide

UNC supports multiple AI providers for code review. Learn how to configure and use each one.

## Supported Providers

- **OpenAI** - GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Anthropic** - Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Mistral** - Mistral-large, Mistral-small, Codestral
- **Google Gemini** - Gemini-2.5-flash, Gemini-2.5-pro, Gemini-1.5-pro
- **Ollama** - Local models (codellama, tinyllama, etc.)

## OpenAI

### Setup

1. **Get API Key**
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key

2. **Configure UNC**
   ```bash
   # Set provider
   unc config set ai.provider openai
   
   # Set API key
   unc config set ai.openai_api_key "sk-..."
   
   # Set model
   unc config set ai.model "gpt-4-turbo"
   ```

3. **Environment Variable (Alternative)**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

### Configuration
```yaml
ai:
  provider: "openai"
  model: "gpt-4-turbo"
  temperature: 0.1
  max_tokens: 4000
  openai_api_key: "sk-..."  # or use environment variable
  openai_base_url: null     # Optional custom base URL
```

### Available Models
- `gpt-4-turbo` (recommended)
- `gpt-4`
- `gpt-3.5-turbo`
- `gpt-4o`

## Anthropic

### Setup

1. **Get API Key**
   - Visit [Anthropic Console](https://console.anthropic.com/)
   - Create a new API key

2. **Configure UNC**
   ```bash
   # Set provider
   unc config set ai.provider anthropic
   
   # Set API key
   unc config set ai.anthropic_api_key "sk-ant-..."
   
   # Set model
   unc config set ai.model "claude-3-sonnet-20240229"
   ```

3. **Environment Variable (Alternative)**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

### Configuration
```yaml
ai:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  temperature: 0.1
  max_tokens: 4000
  anthropic_api_key: "sk-ant-..."  # or use environment variable
```

### Available Models
- `claude-3-opus-20240229` (most capable)
- `claude-3-sonnet-20240229` (balanced)
- `claude-3-haiku-20240307` (fastest)

## Mistral

### Setup

1. **Get API Key**
   - Visit [Mistral AI Platform](https://console.mistral.ai/)
   - Create a new API key

2. **Configure UNC**
   ```bash
   # Set provider
   unc config set ai.provider mistral
   
   # Set API key
   unc config set ai.mistral_api_key "your-api-key"
   
   # Set model
   unc config set ai.model "mistral-large-latest"
   ```

3. **Environment Variable (Alternative)**
   ```bash
   export MISTRAL_API_KEY="your-api-key"
   ```

### Configuration
```yaml
ai:
  provider: "mistral"
  model: "mistral-large-latest"
  temperature: 0.1
  max_tokens: 4000
  mistral_api_key: "your-api-key"  # or use environment variable
```

### Available Models
- `mistral-large-latest` (most capable, higher cost)
- `mistral-small-latest` (balanced performance and cost)
- `codestral-latest` (specialized for code generation)
- `mistral-moderation-latest` (content moderation)

## Google Gemini

### Setup

1. **Get API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key

2. **Configure UNC**
   ```bash
   # Set provider
   unc config set ai.provider gemini
   
   # Set API key
   unc config set ai.gemini_api_key "AIza..."
   
   # Set model
   unc config set ai.model "gemini-2.0-flash-exp"
   ```

3. **Environment Variable (Alternative)**
   ```bash
   export GEMINI_API_KEY="AIza..."
   ```

### Configuration
```yaml
ai:
  provider: "gemini"
  model: "gemini-2.0-flash-exp"
  temperature: 0.1
  max_tokens: 4000
  gemini_api_key: "AIza..."  # or use environment variable
  gemini_base_url: null      # Optional custom base URL
```

### Available Models
- `gemini-2.0-flash-exp` (recommended)
- `gemini-2.0-pro-exp`
- `gemini-1.5-pro`

## Ollama

### Setup

1. **Install Ollama**
   - Visit [Ollama.ai](https://ollama.ai/)
   - Download and install for your platform

2. **Pull a Model**
   ```bash
   # Pull a code-focused model
   ollama pull codellama:7b
   
   # Or a smaller model
   ollama pull tinyllama
   ```

3. **Configure UNC**
   ```bash
   # Set provider
   unc config set ai.provider ollama
   
   # Set model
   unc config set ai.ollama_model "codellama:7b"
   
   # Set base URL (if different from default)
   unc config set ai.ollama_base_url "http://localhost:11434"
   ```

### Configuration
```yaml
ai:
  provider: "ollama"
  model: "codellama:7b"
  temperature: 0.1
  max_tokens: 4000
  ollama_base_url: "http://localhost:11434"
  ollama_model: "codellama:7b"
```

### Recommended Models
- `codellama:7b` - Good balance of speed and quality
- `codellama:13b` - Higher quality, slower
- `tinyllama` - Fast, smaller model
- `llama3.2:3b` - Fast, good for quick reviews

## Testing Your Setup

After configuring a provider, test it:

```bash
# Test with a simple review
unc review run-review --verbose

# Check configuration
unc config show
```

## Troubleshooting

### API Key Issues
```bash
# Check if API key is set
unc config show

# Test API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

## Next Steps

- **[Configuration Guide](configuration.md)** - More configuration options
- **[Examples](examples.md)** - Usage examples for each provider
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions 