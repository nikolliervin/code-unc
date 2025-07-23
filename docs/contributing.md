# Contributing

Thank you for your interest in contributing to UNC!

## Development Setup

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

## Project Structure

```
unc/
├── configs/                 # Configuration files
│   ├── default.yaml        # Default configuration
│   └── prompts/           # AI prompt templates
├── src/
│   └── code_review_cli/
│       ├── cli/           # Command-line interface
│       ├── core/          # Core functionality
│       │   ├── ai/        # AI provider clients
│       │   ├── cache/     # Caching system
│       │   ├── config/    # Configuration management
│       │   ├── git/       # Git integration
│       │   └── output/    # Output formatting
│       └── models/        # Data models
├── tests/                 # Test suite
├── pyproject.toml        # Project configuration
└── README.md            # Project documentation
```

## Development Guidelines

### Code Style
- Use Black for code formatting
- Use isort for import sorting
- Follow PEP 8 guidelines
- Add type hints to all functions

### Testing
- Write tests for new features
- Ensure all tests pass
- Maintain good test coverage

### Documentation
- Update documentation for new features
- Add docstrings to functions
- Update examples if needed

## License

MIT License - see LICENSE file for details. 