#!/usr/bin/env python3
"""Check JIRA tickets for AAP Gateway releases.

Extracts commits since the last release tag and identifies associated JIRA tickets.
"""
import argparse
import json
import subprocess
import sys

from release_utils import (
    BRANCH_PREFIX,
    ReleaseError,
    extract_jira_ticket,
    fetch_remote_branch,
    fetch_remote_tags,
    find_previous_tag,
    find_upstream_remote,
    get_commits_since_tag,
    validate_version_format,
)


def check_version_jiras(version: str, remote: str, verbose: bool = True) -> dict:
    """Check JIRA tickets for a single version."""
    branch = f"{BRANCH_PREFIX}{version}"

    if verbose:
        print(f"\n{'=' * 70}")
        print(f"Checking version: {version}")
        print(f"{'=' * 70}\n")

    # Fetch the branch
    fetch_remote_branch(remote, branch, quiet=not verbose)

    # Find previous tag
    previous_tag = find_previous_tag(version)
    if verbose:
        if previous_tag:
            print(f"Previous tag: {previous_tag}")
        else:
            print(f"No previous tag found for version {version}")

    # Get commits since previous tag
    commits = get_commits_since_tag(remote, branch, previous_tag)

    if verbose:
        print(f"Found {len(commits)} commit(s) since {previous_tag or 'beginning'}\n")

    results = []
    for commit in commits:
        jira_key = extract_jira_ticket(commit['message'])
        results.append({'hash': commit['hash'], 'message': commit['message'], 'jira_key': jira_key})

    return {'version': version, 'branch': branch, 'previous_tag': previous_tag, 'commit_count': len(commits), 'commits': results}


def escape_markdown(text: str) -> str:
    """Escape special markdown characters for table safety."""
    return text.replace('|', '\\|').replace('`', '\\`').replace('*', '\\*')


def format_markdown_table(results: list, max_message_length: int = 80) -> str:
    """Format results as markdown table."""
    lines = []

    for version_data in results:
        version = version_data['version']
        previous_tag = version_data['previous_tag'] or 'beginning'
        commit_count = version_data.get('commit_count', 0)

        lines.append(f"\n## Version {version}")
        lines.append(f"Commits since {previous_tag}: {commit_count}\n")

        if commit_count == 0:
            lines.append("No commits found.\n")
            continue

        lines.append("| Commit | JIRA Ticket | Message |")
        lines.append("|--------|-------------|---------|")

        for commit in version_data.get('commits', []):
            hash_short = commit['hash']
            jira = commit['jira_key'] or 'N/A'
            message = escape_markdown(commit['message'])
            if len(message) > max_message_length:
                message = f"{message[:max_message_length - 3]}..."
            lines.append(f"| {hash_short} | {jira} | {message} |")

        lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check JIRA tickets for AAP Gateway releases")

    parser.add_argument('--versions', required=True, help='Version number or comma-separated list (e.g., 2.6 or 2.5,2.6)')
    parser.add_argument('--output-format', choices=['json', 'markdown'], default='json', help='Output format (default: json)')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress messages (only output results)')
    parser.add_argument('--max-message-length', type=int, default=80, help='Maximum length for commit messages in markdown output (default: 80)')

    args = parser.parse_args()
    verbose = not args.quiet

    try:
        # Parse versions
        versions = [v.strip() for v in args.versions.split(',')]

        # Validate all versions
        for version in versions:
            validate_version_format(version)

        # Find remote
        remote = find_upstream_remote()
        if verbose:
            print(f"Using remote: {remote}")

        # Fetch tags once
        fetch_remote_tags(remote, quiet=not verbose)

        # Check each version
        results = []
        has_errors = False

        for version in versions:
            try:
                result = check_version_jiras(version, remote, verbose)
                result['success'] = True
                results.append(result)
            except ReleaseError as e:
                print(f"ERROR checking version {version}: {e}", file=sys.stderr)
                results.append({'version': version, 'error': str(e), 'success': False})
                has_errors = True
                # Continue checking other versions to show all errors at once

        # Output results
        if args.output_format == 'json':
            output = {
                'versions': results,
                'total_versions': len(versions),
                'total_commits': sum(r.get('commit_count', 0) for r in results),
                'success': not has_errors,
            }
            print(json.dumps(output, indent=2))
        else:  # markdown
            print(format_markdown_table(results, args.max_message_length))

        # Exit with error if any version failed
        sys.exit(1 if has_errors else 0)

    except ReleaseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Git command failed: {e}", file=sys.stderr)
        if e.stderr:
            print(f"Details: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
