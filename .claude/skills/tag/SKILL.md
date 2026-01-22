---
name: tag
description: "Create release tags for AAP Gateway with JIRA validation. Use when: (1) Creating release tags on stable branches, (2) Validating JIRA tickets before releases, (3) Checking release note completeness, (4) Ensuring proper JIRA status and target version fields before tagging."
---

# Tag - Create Release Tags for AAP Gateway

This skill automates the process of creating release tags on stable branches with JIRA validation.

## Prerequisites

**MANDATORY FIRST STEP:** Before proceeding with any other steps, you MUST:

1. Check if `AGENTS.md` exists in the workspace root and read it
2. Check if `AGENTS_USER.md` exists in the workspace root and read it (if present)
3. Verify you understand:
   - JIRA credentials and comment formatting requirements
   - Git workflow with forked repositories

**If these files don't exist**, proceed with the skill but be aware that you may not have complete context about:
- JIRA authentication setup
- Git remote configuration
- Project-specific conventions

**DO NOT SKIP THIS STEP.** These files contain critical information about how to interact with JIRA, git remotes, and other systems.

**MCP Server Check:**
- Verify that JIRA MCP tools are available for retrieving issue details
- If JIRA MCP server is not configured, inform the user that JIRA validation will be skipped
- The skill can still create tags without JIRA validation

## Input Parameters

The skill accepts up to 3 positional arguments, parsed in order:

### Argument 1: Version (required)
The major.minor version or comma-separated list of versions
- Examples: `2.6`, `2.5`, or `2.5,2.6`
- Format: `X.Y` where X and Y are integers
- If not provided, prompt the user for the version(s)
- When multiple versions are provided, tags will be created for all of them

### Argument 2: Tag Suffix (required)
The tag suffix to append to the version
- Examples: `20251119`, `20260101`, `20251119-2`
- The tag suffix will be in the YYYYMMDD format, with an optional `-[0-9]` suffix
- If not provided, prompt the user for the tag suffix
- This suffix will be used for all versions specified
- **Note:** Tag suffixes may contain future dates - this is acceptable and expected for release planning purposes

### Argument 3: Commit Hash (optional)
A specific git commit hash to tag
- Examples: `abc123def`, `766f8411`
- If provided, use this specific commit for the tag
- Otherwise, the script will use the latest commit from each stable branch
- **Note:** Only works when tagging a single version. Do not use when tagging multiple branches.

## Workflow

### Step 1: Load JIRA Field Constants

Before processing commits, read the JIRA field ID constants from the Python utilities:

1. Read `.claude/skills/tag/scripts/release_utils.py`
2. Extract the values of these constants:
   - `JIRA_FIELD_TARGET_VERSION`
   - `JIRA_FIELD_RELEASE_NOTE_TYPE`
   - `JIRA_FIELD_RELEASE_NOTE`
3. Store these values for use in all subsequent JIRA MCP queries

These field IDs will be used throughout the validation process.

### Step 2: Extract Commits and JIRA Tickets

Run the commit extraction script to get commits and their associated JIRA ticket references:

```bash
python3 .claude/skills/tag/scripts/check_release_jiras.py \
  --versions {versions} \
  --quiet
```

This script extracts commits since the previous tag for each version and identifies JIRA ticket numbers from commit messages. It does NOT query JIRA - that's done by Claude in Step 2.

**Parsing the output:**
The JSON structure is:
```json
{
  "versions": [
    {
      "version": "2.6",
      "branch": "stable-2.6",
      "previous_tag": "2.6.20260101",
      "commit_count": 5,
      "commits": [
        {
          "hash": "abc123",
          "message": "[AAP-12345] Fix bug...",
          "jira_key": "AAP-12345"
        }
      ],
      "success": true
    }
  ],
  "total_versions": 1,
  "total_commits": 5,
  "success": true
}
```

**Extract commits for processing:**
1. Check `data['success']` - if false, the script encountered errors
2. For each version, check `data['versions'][i]['success']` - if false, that version failed
3. If any version failed, display the error and abort the skill
4. Access `data['versions'][i]['commits']` to get the list of commits for each version

### Step 3: Query and Validate JIRA Tickets

**IMPORTANT:** Claude performs all JIRA querying and validation using MCP functions. The Python scripts only handle git operations.

**Use the JIRA field IDs extracted in Step 1** for all queries and validation logic below.

**Grouping commits by JIRA:**
1. Iterate through all commits from `data['versions'][i]['commits']`
2. Group commits by their `jira_key` field (may be null for commits without JIRA tickets)
3. Create a mapping: `jira_key → [list of commit hashes]`
4. For commits with `jira_key: null`, attempt to find JIRA ticket from PR:
   - Extract PR number from commit message using pattern `#(\d+)`
   - If PR number found, run: `gh pr view {number} --repo ansible-automation-platform/aap-gateway --json title,body --jq '(.title + " " + .body)'`
   - Search the output for JIRA pattern `AAP-\d+`
   - If JIRA found in PR, update the commit's `jira_key` and regroup
   - If any error occurs (no PR number, PR not found, gh unavailable), keep as null and note the error for the warning message
5. Group remaining commits with `jira_key: null` under a special "N/A" key
6. Extract unique JIRA tickets (skip null/N/A keys for queries)

**Query JIRA tickets using MCP:**
For each unique `jira_key`, use the JIRA MCP's issue retrieval tool. Build the fields parameter using the constants extracted in Step 1:
- issue_key: "{jira_key}"
- fields: "summary,status," + JIRA_FIELD_TARGET_VERSION + "," + JIRA_FIELD_RELEASE_NOTE_TYPE + "," + JIRA_FIELD_RELEASE_NOTE

**Important:** MCP functions are only available to Claude, not to subprocess Python scripts. Claude must query all JIRA tickets and perform validation before calling the tag creation script.

**Check for outdated Target Versions:**
- Extract the tag name being created: `{version}.{tag-suffix}` (e.g., "2.6.20260121")
- If a JIRA's Target Version (`JIRA_FIELD_TARGET_VERSION`) contains a previous tag for this version but NOT the current tag being created:
  - **⚠ Warning**: Target Version outdated (points to previous tag)
  - Example: If creating tag "2.6.20260121" and JIRA has Target Version "2.6.20260106" → Warning (let the user decide if this should be updated to 2.6.20260121)
  - Example: If creating tag "2.6.20260121" and JIRA has Target Version "2.6" or "2.6.20260121" → Continue validation normally

**Target Version validation logic:**
For each JIRA ticket being validated, check the Target Version field:
1. **Check for exact tag match**: Does Target Version include "2.6.20260121" (the full tag name)?
   - If YES → ✓ Valid (product enhancement for customers)
   - If NO → Continue to step 2
2. **Check for version match**: Does Target Version include "2.6" (the version)?
   - If YES → ⚠ Warning (acceptable for internal-only changes; user should confirm this is not a customer-facing product enhancement)
   - If NO → ✗ Error (Target Version mismatch)

**Why the warning for version-only (e.g., "2.6")?**
- Target Version "2.6" (without full tag) is **acceptable and correct** for internal-only changes like:
  - GitHub workflows, CI/CD tooling
  - Development tooling, scripts
  - Internal refactoring, test improvements
  - Anything customers will never see
- Target Version should be the **full tag** (e.g., "2.6.20260121") for product enhancements:
  - Bug fixes customers will see
  - New features, improvements
  - API changes, behavior changes
  - Anything in release notes

The warning prompts the user to confirm that "2.6" is intentional (internal-only) and not a customer-facing change that should have the full tag.

**Validation rules:**

**ERRORS (require user confirmation to proceed):**
1. **JIRA ticket doesn't exist** - Commit references ticket but it's not found in JIRA
2. **Target Version mismatch** - Target Version field exists but doesn't include the release version (X.Y) being tagged
   - Example: Creating tag "2.6.20260121" but Target Version is "2.7" or "aap-devel"
3. **Invalid status** - Status is not "Release Pending" or "Closed" (e.g., "New", "In Progress", "In Review", etc.)
4. **Missing Release Note** - Release Note is empty when Release Note Type is not "Release Note Not Required"

**WARNINGS (informational, user can proceed):**
1. **No JIRA ticket found** - Commit message and PR (if available) don't reference any AAP-XXXXX ticket. Include any PR lookup errors in the warning.
2. **Missing Target Version** - Target Version field is empty
3. **Target Version missing tag** - Target Version includes the version (e.g., "2.6") but not the full tag (e.g., "2.6.20260121")
   - This is **acceptable for internal-only changes** (tooling, workflows, refactoring)
   - User should confirm this is not a customer-facing product enhancement
4. **Target Version outdated** - Target Version contains a previous tag (e.g., "2.6.20260106") but not the current tag being created
5. **Closed status** - Issue is already in "Closed" state (informational)

**Notes:**
- Release Note Type missing is not validated (JIRA automation ensures it's populated)
- Acceptable statuses: "Release Pending" (OK), "Closed" (WARNING)
- All other statuses are ERRORs

**Error Handling:**
- JIRA API unavailable: ERROR, offer to skip validation
- Rate limiting: Pause and inform user

### Step 4: Display Validation Results

Create a markdown table showing JIRA tickets (deduplicated) and their validation status:

**Table Columns:**
- **JIRA:** JIRA ticket key or "N/A"
- **Commits:** Count of commits or comma-separated hashes if ≤3 commits
- **Validation:** Overall validation status icon
  - ✓ = All checks passed (no errors or warnings)
  - ⚠ = Has warnings but no errors
  - ✗ = Has errors (blocking issues)
- **Target Version:** Value from `JIRA_FIELD_TARGET_VERSION` or "Missing"
- **Release Note:** "Present", "Not Required", or "Missing"
- **Status:** JIRA status name
- **Issues:** Comma-separated list of specific problems, or "None"

**Example Table:**
```
| JIRA | Commits | Validation | Target Version | Release Note | Status | Issues |
|------|---------|------------|----------------|--------------|--------|--------|
| AAP-12345 | abc123 | ✓ | 2.6.20260121 | Present | Release Pending | None |
| AAP-67890 | def456, ghi789 | ⚠ | 2.6 | Not Required | Closed | Target Version missing tag (confirm internal-only), Closed status |
| AAP-11111 | jkl012 | ✗ | 2.7 | Present | Release Pending | Target Version mismatch (has 2.7, tagging 2.6) |
| AAP-22222 | 3 commits | ✗ | 2.6 | Missing | In Progress | Missing Release Note, Invalid status |
| AAP-33333 | mno345 | ⚠ | 2.6.20260106 | Present | Closed | Target Version outdated (previous tag), Closed status |
| AAP-44444 | stu901 | ⚠ | 2.6 | Present | Release Pending | Target Version missing tag (confirm internal-only) |
| N/A | pqr678 | ⚠ | N/A | N/A | N/A | No JIRA ticket (checked PR #123, not found) |
```

**Summary:**
- Total unique JIRAs: X
- Valid (✓): Y JIRAs
- Warnings (⚠): Z JIRAs (non-blocking)
- Errors (✗): W JIRAs (blocking)

### Step 5: Handle Validation Issues

**If no issues (all ✓):** Proceed directly to Step 6

**If only warnings (⚠, no ✗):**
- Inform user of warnings with details:
  - "Target Version missing tag" warnings: List each JIRA and ask user to confirm these are internal-only changes (tooling, workflows, refactoring) and not customer-facing enhancements
  - Other warnings: Missing JIRA tickets, Closed status, etc.
- Ask: Proceed with tagging, review details, or abort?
- Warnings don't require fixes - user confirms and can proceed

**If any errors (✗):**
- **Strongly recommend** fixing errors before proceeding
- Display specific issues for each error (e.g., "AAP-12345: Status is In Progress, AAP-67890: Target Version mismatch")
- Offer options:
  1. **Fix issues first** (Recommended) - Exit and provide detailed list
  2. **Continue anyway** - Proceed despite errors (requires confirmation)
  3. **Abort** - Cancel tagging

**If multiple versions with mixed results:**
- Example: Version 2.5 has errors, 2.6 is clean
- Offer to tag only clean versions (2.6)

**If JIRA API unavailable:**
- Cannot validate any tickets
- Offer: Skip validation and proceed, or abort

After user decides: exit (if fixing/aborting) or continue to Step 6.

### Step 6: Preview Tag Creation

For each version, execute these commands to gather preview information:

**Find upstream remote:**
```bash
remote=$(git remote -v | grep 'ansible-automation-platform' | awk 'NR==1{print $1}')
```

**For each version:**

1. Fetch branch and tags:
```bash
git fetch $remote stable-{version}
git fetch --tags $remote
```

2. Determine commit to tag:
   - If commit hash specified: use it directly
   - Otherwise: `commit=$(git log $remote/stable-{version} -1 --format=%H)`

3. Find previous tag:
```bash
previous_tag=$(git tag -l "{version}.*" --sort=-version:refname | head -1)
```

4. Count commits since previous tag:
```bash
git log ${previous_tag}...$remote/stable-{version} --oneline --no-merges | wc -l
```

Display table for all versions:
- Tag name: `{version}.{tag-suffix}`
- Commit: `{commit hash}`
- Previous tag: `{previous_tag}` or "none"
- Commits included: `{count}`

### Step 7: Confirm Tag Creation

Ask user: "How would you like to proceed?"

Options:
1. Create tags locally only
2. Create and push tags
3. Abort

### Step 8: Execute Tag Creation

**If "Abort":** Exit the skill

**If creating tags:**

For each version:

1. Validate commit exists and is in branch history (skip if using latest from branch):
```bash
git cat-file -e {commit} 2>/dev/null || { echo "ERROR: Commit {commit} doesn't exist"; exit 1; }
git merge-base --is-ancestor {commit} $remote/stable-{version} 2>/dev/null || { echo "ERROR: Commit {commit} not in stable-{version} history"; exit 1; }
```

2. Check tag doesn't exist locally:
```bash
if git tag -l "{version}.{tag-suffix}" | grep -q .; then
  echo "ERROR: Tag {version}.{tag-suffix} exists locally. Delete with: git tag -d {version}.{tag-suffix}"
  exit 1
fi
```

3. Create annotated tag:
```bash
git tag -a {version}.{tag-suffix} {commit} -m "{version}.{tag-suffix}"
```

4. If user selected "Create and push tags":
```bash
git push $remote {version}.{tag-suffix}
```

## Completion

Display summary:
- Successfully created tags: `{list}`
- Pushed to remote: `{yes/no}`
- If not pushed: `git push $remote {tag-names}`

**Next steps to communicate to user:**
- If tags were created locally only:
  - Remind them to push with: `git push {remote} {tag-names}`
- If tags were pushed:
  - Verify tags on GitHub: https://github.com/ansible-automation-platform/aap-gateway/tags
  - Provide direct links to the created tags
- Always remind to:
  - Monitor CI/CD pipelines for the tags
  - Update the associated release tracking Jira tickets with the created tags
- If warnings were accepted (missing release notes, target version issues, etc.):
  - Remind to examine and address the specific warnings where appropriate before the release

## Error Handling

**Before Starting:**
- Check if tags exist (local/remote) with `git tag -l` and `git ls-remote --tags`
- If tag exists on remote: Use different suffix (remote tags are permanent)
- If tag exists locally only: Offer to delete with `git tag -d {tag}`

**During Execution:**
- **Tag creation fails:** Display error, offer to retry or abort
- **Push fails:** Keep local tags, provide manual push command
- **Partial success:** Keep successful tags, report failures

**Rollback:**
- Local tags: Safe to delete with `git tag -d {tag}`
- Remote tags: **Cannot be deleted via this skill** - tags are permanent once pushed

**Common Errors:**
- Tag exists: Use different suffix or delete local tag
- Remote not found: Check `git remote -v` for ansible-automation-platform org
- Invalid format: Version must be X.Y
- Branch doesn't exist: Verify branch name/version
- JIRA errors: Check credentials, connectivity, or skip validation

## Notes

- **JIRA validation is performed by Claude** using MCP functions
- **Commit extraction** uses `check_release_jiras.py` script
- **Tag creation and pushing** use direct git commands executed by Claude
- Tags are created as annotated tags with the tag name as the message
- JIRA validation is informational - users can proceed despite warnings
- All git operations are reversible (tags can be deleted locally before pushing)
