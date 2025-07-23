# Examples

Common usage examples for UNC.

## Basic Examples

### Simple Review
```bash
# Review current changes against main branch
unc review run-review
```

### Review Specific Branches
```bash
# Review feature branch against main
unc review run-review --source feature-branch --target main

# Review against a specific commit
unc review run-review --source HEAD --target abc1234
```

### Review with Focus Areas
```bash
# Focus on security issues
unc review run-review --focus security

# Focus on multiple areas
unc review run-review --focus security --focus performance --focus style
```

### Review Specific Files
```bash
# Review only Python files
unc review run-review --include "*.py"

# Exclude test files
unc review run-review --exclude "tests/*" --exclude "*_test.py"

# Combine include and exclude
unc review run-review --include "*.py" --exclude "tests/*"
```

## Output Formats

### Rich Output (Default)
```bash
# Colorful, formatted output
unc review run-review
```

### JSON Output
```bash
# Machine-readable output
unc review run-review --format json

# Save to file
unc review run-review --format json > review.json
```

### Markdown Output
```bash
# Markdown format for documentation
unc review run-review --format markdown > review.md
```

### HTML Output
```bash
# HTML format for web viewing
unc review run-review --format html > review.html
```

## Configuration Examples

### Change AI Provider
```bash
# Switch to OpenAI
unc config set ai.provider openai
unc config set ai.model "gpt-4-turbo"
unc config set ai.openai_api_key "sk-..."

# Switch to Anthropic
unc config set ai.provider anthropic
unc config set ai.model "claude-3-sonnet-20240229"
unc config set ai.anthropic_api_key "sk-ant-..."

# Switch to Ollama
unc config set ai.provider ollama
unc config set ai.ollama_model "codellama:7b"
```

### Adjust Review Settings
```bash
# Set temperature for more creative reviews
unc config set ai.temperature 0.3

# Increase max tokens for longer reviews
unc config set ai.max_tokens 8000

# Change output format
unc config set output.format json
```

## Advanced Examples

### CI/CD Integration
```bash
# In your CI pipeline
unc review run-review --source $CI_COMMIT_SHA --target $CI_COMMIT_BEFORE_SHA --format json > review.json

# Check for critical issues
if jq -e '.issues[] | select(.severity == "CRITICAL")' review.json > /dev/null; then
    echo "Critical issues found!"
    exit 1
fi
```

### Batch Processing
```bash
# Review multiple branches
for branch in feature1 feature2 feature3; do
    echo "Reviewing $branch..."
    unc review run-review --source $branch --target main --format json > "review_$branch.json"
done
```

### Custom Configuration
```bash
# Use custom config file
unc review run-review --config ./production.yaml

# Override settings for this run
unc review run-review --source feature --target main --focus security
```

## History Management

### View Review History
```bash
# List recent reviews
unc history list

# List with limit
unc history list --limit 5

# JSON format
unc history list --format json
```

### Show Specific Review
```bash
# Show review by ID
unc history show abc12345-def6-7890-ghij-klmnopqrstuv

# Get review ID from list and show details
REVIEW_ID=$(unc history list --format json | jq -r '.[0].id')
unc history show $REVIEW_ID
```

### Clear History
```bash
# Clear with confirmation
unc history clear

# Clear without confirmation
unc history clear --yes
```

## Troubleshooting Examples

### Debug Mode
```bash
# Enable verbose output
unc review run-review --verbose

# Check configuration
unc config show

# Validate configuration
unc config validate
```

### API Testing
```bash
# Test OpenAI connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Test Anthropic connection
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/models

# Test Ollama
curl http://localhost:11434/api/tags
```

## Real-World Scenarios

### Code Review Workflow
```bash
# 1. Make your changes
git checkout -b feature/new-feature
# ... make changes ...

# 2. Review your changes
unc review run-review --source feature/new-feature --target main

# 3. Address issues and commit
# ... fix issues ...
git add .
git commit -m "Fix issues found by UNC"

# 4. Review again
unc review run-review --source feature/new-feature --target main
```

### Team Integration
```bash
# Set up team configuration
unc config set ai.provider openai
unc config set ai.model "gpt-4-turbo"
unc config set output.format json

# Share configuration
cp ~/.config/unc/config.yaml ./team-config.yaml
git add team-config.yaml
git commit -m "Add team UNC configuration"
```

### Documentation Generation
```bash
# Generate review documentation
unc review run-review --format markdown > REVIEW.md

# Add to pull request
echo "## Code Review" >> PR_DESCRIPTION.md
cat REVIEW.md >> PR_DESCRIPTION.md
```

## Next Steps

- **[Commands Reference](commands.md)** - Complete command reference
- **[AI Providers Guide](ai-providers.md)** - AI provider setup
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions 