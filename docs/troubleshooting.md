# Troubleshooting

Common issues and solutions for UNC.

## Common Issues

### 1. Command Not Found
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

### 2. Configuration Not Found
```bash
# Initialize configuration
unc config init
```

### 3. API Key Issues
```bash
# Check configuration
unc config show

# Validate configuration
unc config validate
```

### 4. Git Repository Issues
```bash
# Ensure you're in a git repository
git status

# Check if branches exist
git branch -a
```

### 5. No Files to Review
```bash
# Check what files are being excluded
unc review run-review --verbose

# Include more file types
unc review run-review --include "*.py" --include "*.js"
```

## AI Provider Issues

### OpenAI Issues

**API Key Problems:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test with curl
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**Rate Limiting:**
```bash
# Reduce request frequency
unc config set ai.retry_delay 2.0
unc config set ai.max_retries 5
```

### Anthropic Issues

**API Key Problems:**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test with curl
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/models
```

### Gemini Issues

**API Key Problems:**
```bash
# Check API key
echo $GEMINI_API_KEY

# Test with curl
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GEMINI_API_KEY"
```

### Ollama Issues

**Connection Problems:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**Model Not Found:**
```bash
# List available models
ollama list

# Pull the model
ollama pull codellama:7b
```

## Performance Issues

### Slow Reviews
```bash
# Use a faster model
unc config set ai.model "gpt-3.5-turbo"  # Instead of gpt-4

# Reduce max tokens
unc config set ai.max_tokens 2000

# Use Ollama for local processing
unc config set ai.provider ollama
unc config set ai.ollama_model "tinyllama"
```

### Large Diffs
```bash
# Increase diff size limit
unc config set git.max_diff_size 5000000  # 5MB

# Review specific files only
unc review run-review --include "*.py"
```

## Debug Mode

Enable verbose output for debugging:

```bash
unc review run-review --verbose
```

## Cache Management

Clear cache if you encounter issues:

```bash
# Clear review history
unc history clear --yes

# Or manually delete cache directory
rm -rf ~/.cache/unc/
```

## Environment Variables

Set these environment variables for API keys:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google Gemini
export GEMINI_API_KEY="your-gemini-api-key"
```

## Configuration Issues

### Invalid Configuration
```bash
# Validate configuration
unc config validate

# Reset to defaults
rm ~/.config/unc/config.yaml
unc config init
```

### Configuration File Location
```bash
# Check config file location
unc config show

# Use custom config file
unc review run-review --config ./custom-config.yaml
```

## Network Issues

### Proxy Configuration
```bash
# Set proxy environment variables
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"

# Or configure in UNC
unc config set ai.openai_base_url "http://proxy.company.com/openai"
```

### SSL Issues
```bash
# Disable SSL verification (not recommended for production)
export PYTHONHTTPSVERIFY=0
```

## Getting Help

### Check Version
```bash
unc version
```

### Get Help
```bash
# Comprehensive help
unc help

# Command-specific help
unc review --help
unc config --help
unc history --help
```

### Logs
```bash
# Enable debug logging
export UNC_DEBUG=1
unc review run-review --verbose
```

## Common Error Messages

### "No changes to review"
- Ensure you're in a git repository
- Check if there are differences between branches
- Verify branch names are correct

### "API key not found"
- Set the API key in configuration
- Use environment variables
- Check API key format

### "Model not found"
- Verify model name is correct
- Check if model is available for your provider
- For Ollama, ensure model is pulled

### "Connection timeout"
- Check internet connection
- Verify API endpoints are accessible
- Increase timeout settings

## Next Steps

- **[Installation Guide](installation.md)** - Reinstall if needed
- **[Configuration Guide](configuration.md)** - Fix configuration issues
- **[AI Providers Guide](ai-providers.md)** - Provider-specific setup
- **[Examples](examples.md)** - Working examples 