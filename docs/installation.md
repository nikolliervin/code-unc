# Installation Guide

This guide will help you install UNC on your system.

## Prerequisites

- Python 3.8 or higher
- Git repository
- AI provider API key (depending on your choice)

## Install from Source

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/nikolliervin/code-unc.git
cd code-unc
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install UNC

```bash
# Install in development mode
pip install -e .
```

## Adding to PATH

After installation, you may need to add the `unc` command to your system PATH to use it from anywhere in the terminal.

### Windows

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

### macOS/Linux

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

## Verify Installation

After adding to PATH, verify the installation:

```bash
# Check if unc is available
unc version

# Or check the help
unc help
```

If you get a "command not found" error, restart your terminal or reload your shell profile.

## Next Steps

After successful installation:

1. **[Quick Start Guide](quick-start.md)** - Get up and running
2. **[Configuration Guide](configuration.md)** - Set up your AI provider
3. **[AI Providers Guide](ai-providers.md)** - Choose and configure your AI provider

## Troubleshooting

If you encounter issues during installation, see the [Troubleshooting Guide](troubleshooting.md) for common solutions. 