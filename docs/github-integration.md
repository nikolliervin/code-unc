# GitHub Integration

Learn how to integrate UNC with GitHub to automatically review pull requests.

## Overview

UNC can be integrated with GitHub using GitHub Actions to automatically review pull requests and post comments with AI-generated feedback.

## Setup

### 1. Add GitHub Action Workflow

**Basic Version** (`.github/workflows/code-review.yml`):
Use the simple workflow for basic integration with general comments.

**Inline Comments Version** (`.github/workflows/code-review-inline-simple.yml`):
Use this workflow for **line-by-line comments** on specific code lines:
- Comments appear directly on the problematic lines
- More precise feedback
- Better developer experience
- Works with existing JSON output format

**Advanced Version** (`.github/workflows/code-review-advanced.yml`):
Use the advanced workflow for production environments with:
- Pre-flight checks for PR size
- Smart focus area detection
- Better error handling
- Cost management
- Performance optimization

Create `.github/workflows/code-review.yml` in your repository:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  code-review:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install UNC
      run: |
        pip install -e .
    
    - name: Configure UNC
      run: |
        unc config set ai.provider ${{ secrets.AI_PROVIDER }}
        unc config set ai.model ${{ secrets.AI_MODEL }}
        
        if [ "${{ secrets.AI_PROVIDER }}" = "openai" ]; then
          unc config set ai.openai_api_key ${{ secrets.OPENAI_API_KEY }}
        elif [ "${{ secrets.AI_PROVIDER }}" = "anthropic" ]; then
          unc config set ai.anthropic_api_key ${{ secrets.ANTHROPIC_API_KEY }}
        elif [ "${{ secrets.AI_PROVIDER }}" = "gemini" ]; then
          unc config set ai.gemini_api_key ${{ secrets.GEMINI_API_KEY }}
        fi
        
        unc config set output.format markdown
    
    - name: Run AI Code Review
      id: review
      run: |
        unc review run-review \
          --source ${{ github.event.pull_request.head.sha }} \
          --target ${{ github.event.pull_request.base.sha }} \
          --format markdown > review.md
        
        REVIEW_CONTENT=$(cat review.md)
        REVIEW_CONTENT="${REVIEW_CONTENT//'%'/'%25'}"
        REVIEW_CONTENT="${REVIEW_CONTENT//$'\n'/'%0A'}"
        REVIEW_CONTENT="${REVIEW_CONTENT//$'\r'/'%0D'}"
        
        echo "review_content<<EOF" >> $GITHUB_OUTPUT
        echo "$REVIEW_CONTENT" >> $GITHUB_OUTPUT
        echo "EOF" >> $GITHUB_OUTPUT
    
    - name: Comment on Pull Request
      uses: actions/github-script@v7
      with:
        script: |
          const reviewContent = `${{ steps.review.outputs.review_content }}`;
          
          const hasIssues = reviewContent.includes('## Issues Found') || 
                           reviewContent.includes('### High Severity') ||
                           reviewContent.includes('### Medium Severity') ||
                           reviewContent.includes('### Low Severity');
          
          let commentBody = `## 🤖 AI Code Review\n\n`;
          commentBody += `**Review ID:** ${context.runId}\n`;
          commentBody += `**AI Provider:** ${process.env.AI_PROVIDER}\n`;
          commentBody += `**Model:** ${process.env.AI_MODEL}\n\n`;
          
          if (hasIssues) {
            commentBody += `⚠️ **Issues Found**\n\n`;
            commentBody += reviewContent;
          } else {
            commentBody += `✅ **No issues found!**\n\n`;
            commentBody += reviewContent;
          }
          
          commentBody += `\n---\n`;
          commentBody += `*This review was generated automatically by [UNC](https://github.com/nikolliervin/code-unc)*`;
          
          // Delete previous comments from this bot
          const comments = await github.rest.issues.listComments({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: context.issue.number,
          });
          
          for (const comment of comments.data) {
            if (comment.user.login === 'github-actions[bot]' && 
                comment.body.includes('AI Code Review')) {
              await github.rest.issues.deleteComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: comment.id,
              });
            }
          }
          
          await github.rest.issues.createComment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: context.issue.number,
            body: commentBody,
          });
      env:
        AI_PROVIDER: ${{ secrets.AI_PROVIDER }}
        AI_MODEL: ${{ secrets.AI_MODEL }}
```

### 2. Configure Repository Secrets

Go to your repository settings → Secrets and variables → Actions, and add:

**Required Secrets:**
- `AI_PROVIDER`: The AI provider to use (`openai`, `anthropic`, `gemini`, `ollama`)
- `AI_MODEL`: The model name to use

**Provider-specific Secrets:**
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (if using Anthropic)
- `GEMINI_API_KEY`: Your Gemini API key (if using Gemini)

### 3. Example Configuration

**For OpenAI:**
```
AI_PROVIDER: openai
AI_MODEL: gpt-4-turbo
OPENAI_API_KEY: sk-...
```

**For Anthropic:**
```
AI_PROVIDER: anthropic
AI_MODEL: claude-3-sonnet-20240229
ANTHROPIC_API_KEY: sk-ant-...
```

**For Gemini:**
```
AI_PROVIDER: gemini
AI_MODEL: gemini-2.0-flash-exp
GEMINI_API_KEY: AIza...
```

## How It Works

1. **Trigger**: When a pull request is opened, updated, or reopened
2. **Checkout**: The action checks out the full repository history
3. **Install**: UNC is installed in the GitHub Actions environment
4. **Configure**: UNC is configured with your AI provider settings
5. **Review**: UNC runs a review comparing the PR branch to the base branch
6. **Comment**: The results are posted as a comment on the pull request

## Customization

### Focus Areas
Add focus areas to the review:

```yaml
- name: Run AI Code Review
  run: |
    unc review run-review \
      --source ${{ github.event.pull_request.head.sha }} \
      --target ${{ github.event.pull_request.base.sha }} \
      --focus security \
      --focus performance \
      --format markdown > review.md
```

### File Filtering
Include or exclude specific files:

```yaml
- name: Run AI Code Review
  run: |
    unc review run-review \
      --source ${{ github.event.pull_request.head.sha }} \
      --target ${{ github.event.pull_request.base.sha }} \
      --include "*.py" \
      --exclude "tests/*" \
      --format markdown > review.md
```

### Conditional Reviews
Only run reviews on certain conditions:

```yaml
- name: Run AI Code Review
  if: github.event.pull_request.changed_files < 50  # Only for small PRs
  run: |
    unc review run-review \
      --source ${{ github.event.pull_request.head.sha }} \
      --target ${{ github.event.pull_request.base.sha }} \
      --format markdown > review.md
```

## Example Output

The GitHub Action will post comments like:

```markdown
## 🤖 AI Code Review

**Review ID:** 123456789
**AI Provider:** openai
**Model:** gpt-4-turbo

⚠️ **Issues Found**

### High Severity
- **Security Issue:** Potential SQL injection vulnerability in `src/database.py:42`
- **Performance Issue:** Inefficient algorithm in `src/algorithm.py:15`

### Medium Severity
- **Style Issue:** Missing docstring in `src/utils.py:8`

---

*This review was generated automatically by [UNC](https://github.com/nikolliervin/code-unc)*
```

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your API key is correctly set in repository secrets
   - Check that the provider and model are compatible

2. **Permission Issues**
   - Ensure the GitHub Action has permission to comment on pull requests
   - Check that the repository allows GitHub Actions

3. **Large Diffs**
   - For large pull requests, consider adding file filters
   - Increase timeout settings if needed

### Debug Mode

Add debug output to the workflow:

```yaml
- name: Run AI Code Review
  run: |
    unc review run-review \
      --source ${{ github.event.pull_request.head.sha }} \
      --target ${{ github.event.pull_request.base.sha }} \
      --verbose \
      --format markdown > review.md
```

## Next Steps

- **[Installation Guide](installation.md)** - Install UNC locally
- **[Configuration Guide](configuration.md)** - Configure AI providers
- **[Examples](examples.md)** - More usage examples 