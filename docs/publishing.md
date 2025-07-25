# Publishing UNC to PyPI

This guide explains how to publish UNC to PyPI for distribution.

## Prerequisites

1. **PyPI Account**: Create an account on [PyPI](https://pypi.org)
2. **TestPyPI Account**: Create an account on [TestPyPI](https://test.pypi.org)
3. **Build Tools**: Install build tools

```bash
pip install build twine
```

## Build Configuration

### 1. Update pyproject.toml

Ensure your `pyproject.toml` has the correct package information:

```toml
[project]
name = "code-unc"
version = "0.1.0"
description = "AI-powered code review tool using git diff and various AI providers"
authors = [
    {name = "Ervin Nikolli", email = "your-email@example.com"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Testing",
]

[project.scripts]
unc = "code_review_cli.__main__:main"

[project.urls]
Homepage = "https://github.com/nikolliervin/code-unc"
Repository = "https://github.com/nikolliervin/code-unc"
Issues = "https://github.com/nikolliervin/code-unc/issues"
```

### 2. Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build
```

### 3. Test on TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ code-unc
```

### 4. Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

## GitHub Actions Workflow

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## Version Management

### 1. Semantic Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### 2. Update Version

```bash
# Update version in pyproject.toml
# Then build and publish
python -m build
twine upload dist/*
```

## Security

### 1. API Token

Use PyPI API token instead of password:

1. Go to PyPI → Account Settings → API tokens
2. Create a new token
3. Add to GitHub secrets as `PYPI_API_TOKEN`

### 2. Two-Factor Authentication

Enable 2FA on your PyPI account for additional security.

## Troubleshooting

### Common Issues

1. **Package Name Conflict**
   - Check if `code-unc` is available on PyPI
   - Consider alternative names if needed

2. **Build Errors**
   - Ensure all dependencies are in `pyproject.toml`
   - Check Python version compatibility

3. **Upload Errors**
   - Verify PyPI credentials
   - Check package name availability

## Next Steps

After publishing to PyPI, update the GitHub Action workflow to use:

```yaml
- name: Install UNC
  run: |
    pip install code-unc
```

Instead of installing from GitHub. 