# Cursor Configuration for AAP Gateway

This directory contains Cursor CLI configuration and commands for the AAP Gateway project.

## Directory Structure

- **`commands/`**: Custom slash commands that can be invoked with `/command-name`
  - `pr-review.md`: Automated PR review command using GitHub MCP

## Running PR Reviews Locally

You can run the automated PR review command locally on your development machine to test changes before they run in CI/CD.

### Prerequisites

1. **Cursor CLI**: Install from https://cursor.com/install
2. **Docker**: Required to run the GitHub MCP server
3. **GitHub Personal Access Token**: Create at https://github.com/settings/tokens
   - **Required scopes**:
     - `repo` - Full control of private repositories (required for all PR review operations)
       - Read PR metadata, files, and diffs
       - Create pending reviews
       - Add review comments
       - Submit reviews
   - **Optional scopes**:
     - `read:org` - Read org membership (useful for organization repositories)
4. **GitHub CLI**: Install `gh` CLI and authenticate with `gh auth login`

### Setup

1. **Configure GitHub MCP**:

   Symlink the MCP configuration to your Cursor config directory:
   ```bash
   ln -s "$(pwd)/tools/configs/cursor/pr-review/mcp.json" ~/.cursor/mcp.json
   ```

2. **Create GitHub MCP Environment File**:

   Create a `.github_mcp_env` file in the repository root with your GitHub Personal Access Token:
   ```bash
   echo "GITHUB_PERSONAL_ACCESS_TOKEN=your_github_personal_access_token" > .github_mcp_env
   ```

   This file is used by the GitHub MCP server for authentication. Make sure it's in `.gitignore` to avoid committing credentials.

3. **Set Environment Variables**:
   ```bash
   export CURSOR_API_KEY="your_cursor_api_key"
   export CURSOR_MODEL="claude-sonnet-4-5@20250929"  # or your preferred model
   ```

4. **Set Cursor Config Directory**:
   ```bash
   export CURSOR_CONFIG_DIR="tools/configs/cursor/pr-review/"
   ```

### Running the Review

From the repository root:

```bash
cursor-agent --approve-mcps \
  --model "${CURSOR_MODEL}" \
  --output-format=text \
  --print "/pr-review <OWNER/REPO> <PR_NUMBER>"
```

**Example**:
```bash
cursor-agent --approve-mcps \
  --model "claude-sonnet-4-5@20250929" \
  --output-format=text \
  --print "/pr-review ansible-automation-platform/aap-gateway 1104"
```

### How It Works

1. **GitHub MCP Server**: Runs in a Docker container (pulled automatically on first run)
2. **Authentication**: Uses the `GITHUB_PERSONAL_ACCESS_TOKEN` from `.github_mcp_env` file for GitHub API access
3. **Review Process**:
   - Creates a pending review on the PR
   - Adds review comments with code suggestions to the pending review
   - Submits the complete review with a summary
4. **Output**: Review comments are posted directly to the PR on GitHub

### Notes

- The `--approve-mcps` flag automatically approves MCP server connections
- The command must be run from the repository root where `.cursor/commands/pr-review.md` exists
- All review feedback is posted to GitHub - no local files are created
- The review uses the same workflow as the CI/CD pipeline

## Configuration Files

The PR review command uses configuration from `tools/configs/cursor/pr-review/`:

- **`mcp.json`**: GitHub MCP server configuration (Docker container setup)

## CI/CD Usage

For information about how PR reviews run in GitHub Actions, see:
- `tools/configs/cursor/pr-review/README.md` - CI/CD configuration documentation
- `.github/workflows/cursor-pull-request.yml` - The workflow that runs PR reviews
