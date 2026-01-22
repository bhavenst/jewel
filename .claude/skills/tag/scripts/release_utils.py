#!/usr/bin/env python3
"""Shared utilities for AAP Gateway release management."""
import re
import subprocess
from typing import Optional

# Constants
UPSTREAM_ORG = "ansible-automation-platform"
BRANCH_PREFIX = "stable-"
TAG_VERSION_PATTERN = r'^\d+\.\d+$'

# JIRA patterns and field IDs
JIRA_TICKET_PATTERN = r'AAP-\d+'
JIRA_FIELD_TARGET_VERSION = "customfield_12319940"
JIRA_FIELD_RELEASE_NOTE_TYPE = "customfield_12320850"
JIRA_FIELD_RELEASE_NOTE = "customfield_12317313"


class ReleaseError(Exception):
    """Raised when release operations fail."""


def run_git_command(cmd: list, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Execute a git command and return the result."""
    return subprocess.run(cmd, capture_output=capture_output, text=True, check=check)


def get_git_remotes() -> dict[str, str]:
    """Get all git remotes and their URLs."""
    result = run_git_command(["git", "remote", "-v"])
    remotes = {}
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split()
            if len(parts) >= 2:
                name, url = parts[0], parts[1]
                if name not in remotes:
                    remotes[name] = url
    return remotes


def find_upstream_remote() -> str:
    """Find the remote pointing to ansible-automation-platform organization."""
    remotes = get_git_remotes()

    origin_url = remotes.get('origin', '')
    if UPSTREAM_ORG in origin_url:
        return 'origin'

    for name, url in remotes.items():
        if UPSTREAM_ORG in url:
            return name

    available = '\n'.join([f"  {name}: {url}" for name, url in remotes.items()])
    raise ReleaseError(f"Could not find a remote pointing to {UPSTREAM_ORG} organization.\n Available remotes:\n{available}")


def validate_version_format(version: str) -> None:
    """Validate version format (X.Y)."""
    if not re.match(TAG_VERSION_PATTERN, version):
        raise ReleaseError(f"Version must be in format X.Y (e.g., 2.6), got: {version}")


def get_latest_commit(remote: str, branch: str) -> str:
    """Get the latest commit hash from a remote branch."""
    result = run_git_command(["git", "log", f"{remote}/{branch}", "-1", "--format=%H"])
    return result.stdout.strip()


def find_previous_tag(version: str) -> Optional[str]:
    """Find the latest tag matching the version pattern."""
    pattern = f"{version}.*"
    result = run_git_command(["git", "tag", "-l", pattern, "--sort=-version:refname"], check=False)
    return result.stdout.strip().split('\n')[0] if result.stdout.strip() else None


def get_commits_since_tag(remote: str, branch: str, since_tag: Optional[str]) -> list[dict[str, str]]:
    """Get list of commits since a tag (or all commits if no tag)."""
    range_spec = f"{since_tag}..{remote}/{branch}" if since_tag else f"{remote}/{branch}"

    try:
        result = run_git_command(["git", "log", range_spec, "--oneline", "--no-merges"])
    except subprocess.CalledProcessError as e:
        raise ReleaseError(f"Failed to get commits for {range_spec}: {e.stderr}")

    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                commits.append({'hash': parts[0], 'message': parts[1]})

    return commits


def extract_jira_ticket(message: str) -> Optional[str]:
    """Extract JIRA ticket number from commit message (AAP-XXXXX pattern)."""
    match = re.search(JIRA_TICKET_PATTERN, message)
    return match.group(0) if match else None


def fetch_remote_branch(remote: str, branch: str, quiet: bool = False) -> None:
    """Fetch a specific branch from remote."""
    try:
        run_git_command(["git", "fetch", remote, branch])
        if not quiet:
            print(f"Fetched {remote}/{branch}")
    except subprocess.CalledProcessError as e:
        raise ReleaseError(f"Failed to fetch {remote}/{branch}. Branch or remote may not exist.\n Details: {e.stderr.strip() if e.stderr else str(e)}")


def fetch_remote_tags(remote: Optional[str] = None, quiet: bool = False) -> None:
    """Fetch tags from remote."""
    cmd = ["git", "fetch", "--tags"]
    if remote:
        cmd.insert(2, remote)

    source = f"from {remote}" if remote else "from all remotes"
    try:
        run_git_command(cmd)
        if not quiet:
            print(f"Fetched tags {source}")
    except subprocess.CalledProcessError as e:
        raise ReleaseError(f"Failed to fetch tags {source}: {e.stderr.strip() if e.stderr else str(e)}")
