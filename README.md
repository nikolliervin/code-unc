# UNC - AI-Powered Code Review Tool

AI-powered code review tool using git diff and various AI providers (OpenAI, Anthropic, Gemini, Ollama).

[![GitHub](https://img.shields.io/badge/GitHub-nikolliervin%2Fcode--unc-blue?style=flat&logo=github)](https://github.com/nikolliervin/code-unc)

## Features

- 🤖 **Multiple AI Providers**: Support for OpenAI, Anthropic, Gemini, and Ollama
- 🔍 **Git Integration**: Automatic diff generation and analysis
- 📊 **Rich Output**: Multiple output formats (rich, JSON, markdown, HTML)
- ⚙️ **Flexible Configuration**: Easy setup and customization
- 📝 **Review History**: Track and manage review history
- 🎯 **Focus Areas**: Target specific aspects (security, performance, style)

## Quick Start

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

# Initialize configuration
unc config init

# Run your first review
unc review run-review --source feature-branch --target main
```

### Adding to PATH

To use `unc` from anywhere in your terminal, add it to your system PATH:

**Windows:**
```bash
# Find Python Scripts directory
python -c "import sys; print(sys.executable.replace('python.exe', 'Scripts'))"
# Add the output path to your system PATH environment variable
```

**macOS/Linux:**
```bash
# Add to shell profile
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Verify installation:**
```bash
unc version
```

## Documentation

For comprehensive documentation, see the [docs folder](docs/) or run:

```bash
unc help
```

### Documentation Structure

- **[Installation Guide](docs/installation.md)** - How to install and set up UNC
- **[Quick Start](docs/quick-start.md)** - Get up and running in minutes
- **[Configuration Guide](docs/configuration.md)** - Configure UNC for your needs
- **[Commands Reference](docs/commands.md)** - Complete command reference
- **[AI Providers Guide](docs/ai-providers.md)** - Supported AI providers and setup
- **[Examples](docs/examples.md)** - Common usage examples
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## License

MIT License - see LICENSE file for details. 
