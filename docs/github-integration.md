# GitHub Integration

Learn how to integrate UNC with GitHub to automatically review pull requests.

## Overview

UNC can be integrated with GitHub using GitHub Actions to automatically review pull requests and post both:
- **Inline comments** directly on specific code lines with issues
- **Summary comments** on the pull request with overall feedback and review results

## Setup

### 1. Add GitHub Action Workflow

Create `.github/workflows/code-review.yaml` in your repository:

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
        elif [ "${{ secrets.AI_PROVIDER }}" = "mistral" ]; then
          unc config set ai.mistral_api_key ${{ secrets.MISTRAL_API_KEY }}
        fi
        
        unc config set output.format json
    
    - name: Run AI Code Review
      id: review
      run: |
        unc review run-review \
          --source ${{ github.event.pull_request.head.sha }} \
          --target ${{ github.event.pull_request.base.sha }} \
          --format json > review.json
        
        # Also generate markdown summary
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
    
    - name: Post Inline Comments
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          
          try {
            const reviewData = JSON.parse(fs.readFileSync('review.json', 'utf8'));
            
            if (reviewData.issues && reviewData.issues.length > 0) {
              for (const issue of reviewData.issues) {
                if (issue.file && issue.line) {
                  const comment = `🤖 **${issue.severity.toUpperCase()} - ${issue.category}**\n\n${issue.description}`;
                  
                  try {
                    await github.rest.pulls.createReviewComment({
                      owner: context.repo.owner,
                      repo: context.repo.repo,
                      pull_number: context.issue.number,
                      body: comment,
                      commit_id: '${{ github.event.pull_request.head.sha }}',
                      path: issue.file,
                      line: issue.line,
                    });
                  } catch (error) {
                    console.log(`Failed to post comment on ${issue.file}:${issue.line} - ${error.message}`);
                  }
                }
              }
            }
          } catch (error) {
            console.log('Failed to parse review JSON or post inline comments:', error.message);
          }
    
    - name: Post Summary Comment
      uses: actions/github-script@v7
      with:
        script: |
          const reviewContent = `${{ steps.review.outputs.review_content }}`;
          
          const hasIssues = reviewContent.includes('## Issues Found') || 
                           reviewContent.includes('### High Severity') ||
                           reviewContent.includes('### Medium Severity') ||
                           reviewContent.includes('### Low Severity');
          
          let commentBody = `## 🤖 AI Code Review Summary\n\n`;
          commentBody += `**Review ID:** ${context.runId}\n`;
          commentBody += `**AI Provider:** ${process.env.AI_PROVIDER}\n`;
          commentBody += `**Model:** ${process.env.AI_MODEL}\n\n`;
          
          if (hasIssues) {
            commentBody += `⚠️ **Issues Found** - Check inline comments for details\n\n`;
            commentBody += reviewContent;
          } else {
            commentBody += `✅ **No issues found!**\n\n`;
            commentBody += reviewContent;
          }
          
          commentBody += `\n---\n`;
          commentBody += `*This review was generated automatically by [UNC](https://github.com/nikolliervin/code-unc)*`;
          
          // Delete previous summary comments from this bot
          const comments = await github.rest.issues.listComments({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: context.issue.number,
          });
          
          for (const comment of comments.data) {
            if (comment.user.login === 'github-actions[bot]' && 
                comment.body.includes('AI Code Review Summary')) {
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
- `AI_PROVIDER`: The AI provider to use (`openai`, `anthropic`, `gemini`, `mistral`, `ollama`)
- `AI_MODEL`: The model name to use

**Provider-specific Secrets:**
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (if using Anthropic)
- `GEMINI_API_KEY`: Your Gemini API key (if using Gemini)
- `MISTRAL_API_KEY`: Your Mistral API key (if using Mistral)

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

**For Mistral:**
```
AI_PROVIDER: mistral
AI_MODEL: mistral-large-latest
MISTRAL_API_KEY: ...
```

## How It Works

1. **Trigger**: When a pull request is opened, updated, or reopened
2. **Checkout**: The action checks out the full repository history
3. **Install**: UNC is installed in the GitHub Actions environment
4. **Configure**: UNC is configured with your AI provider settings
5. **Review**: UNC runs a review comparing the PR branch to the base branch (generates both JSON and markdown output)
6. **Inline Comments**: Posts specific comments directly on problematic code lines using the JSON output
7. **Summary Comment**: Posts an overall review summary comment on the pull request using the markdown output

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

The GitHub Action will post two types of comments:

### Inline Comments
Direct comments on specific code lines:

**On line 42 of `src/database.py`:**
```
🤖 **HIGH - SECURITY**

Potential SQL injection vulnerability. Use parameterized queries instead of string concatenation.
```

**On line 15 of `src/algorithm.py`:**
```
🤖 **HIGH - PERFORMANCE**

Inefficient algorithm with O(n²) complexity. Consider using a hash map for O(n) performance.
```

### Summary Comment
Overall review summary on the pull request:

```markdown
## 🤖 AI Code Review Summary

**Review ID:** 123456789
**AI Provider:** openai
**Model:** gpt-4-turbo

⚠️ **Issues Found** - Check inline comments for details

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



## Next Steps

- **[Installation Guide](installation.md)** - Install UNC locally
- **[Configuration Guide](configuration.md)** - Configure AI providers
- **[Examples](examples.md)** - More usage examples 