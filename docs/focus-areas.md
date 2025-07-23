# Focus Areas

UNC can focus on specific aspects of code review. Learn about available focus areas and how to use them.

## Available Focus Areas

### General
- **Description**: General code review covering all aspects
- **Use Case**: Default comprehensive review
- **Command**: `unc review run-review --focus general`

### Security
- **Description**: Security-focused review
- **Use Case**: Identify security vulnerabilities, unsafe practices
- **Command**: `unc review run-review --focus security`

### Performance
- **Description**: Performance-focused review
- **Use Case**: Identify performance bottlenecks, inefficient code
- **Command**: `unc review run-review --focus performance`

### Style
- **Description**: Code style and formatting review
- **Use Case**: Ensure consistent coding standards, readability
- **Command**: `unc review run-review --focus style`

## Using Focus Areas

### Single Focus Area
```bash
# Focus only on security
unc review run-review --focus security

# Focus only on performance
unc review run-review --focus performance
```

### Multiple Focus Areas
```bash
# Focus on security and performance
unc review run-review --focus security --focus performance

# Focus on all areas
unc review run-review --focus general --focus security --focus performance --focus style
```

### Default Focus Areas
You can set default focus areas in your configuration:

```bash
# Set default focus areas
unc config set review.default_focus '["security", "performance"]'
```

## Focus Area Examples

### Security Review
```bash
# Review for security vulnerabilities
unc review run-review --focus security --source feature-branch --target main
```

**What it looks for:**
- SQL injection vulnerabilities
- XSS vulnerabilities
- Insecure authentication
- Hardcoded secrets
- Unsafe file operations

### Performance Review
```bash
# Review for performance issues
unc review run-review --focus performance --source feature-branch --target main
```

**What it looks for:**
- Inefficient algorithms
- Memory leaks
- Unnecessary database queries
- Slow file operations
- Resource-intensive operations

### Style Review
```bash
# Review for code style
unc review run-review --focus style --source feature-branch --target main
```

**What it looks for:**
- Naming conventions
- Code formatting
- Documentation
- Code organization
- Best practices

## Configuration

### Set Default Focus Areas
```yaml
# In your config.yaml
review:
  default_focus:
    - "security"
    - "performance"
```

### Focus Area Prompts
Each focus area uses specialized prompts to guide the AI review:

- **Security**: Emphasizes security best practices and vulnerability detection
- **Performance**: Focuses on efficiency, optimization, and resource usage
- **Style**: Concentrates on code quality, readability, and maintainability
- **General**: Balanced approach covering all aspects

## Best Practices

### When to Use Specific Focus Areas
- **Security**: Before deploying to production, handling sensitive data
- **Performance**: When working on critical paths, large datasets
- **Style**: During code reviews, maintaining team standards
- **General**: Regular development workflow

### Combining Focus Areas
```bash
# For production-ready code
unc review run-review --focus security --focus performance

# For team code reviews
unc review run-review --focus style --focus general

# For critical systems
unc review run-review --focus security --focus performance --focus style
```

## Custom Focus Areas

You can create custom focus areas by modifying the prompt templates in the configuration:

```yaml
# Custom focus area configuration
review:
  custom_focus_areas:
    accessibility:
      description: "Accessibility-focused review"
      prompt: "Focus on accessibility issues..."
    testing:
      description: "Testing-focused review"
      prompt: "Focus on test coverage and quality..."
```

## Next Steps

- **[Commands Reference](commands.md)** - Complete command reference
- **[Examples](examples.md)** - Usage examples with focus areas
- **[Configuration Guide](configuration.md)** - Configure focus areas 