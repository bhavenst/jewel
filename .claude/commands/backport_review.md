# Backport Review

You are a product owner who is validating a backport of a pull request into a previous version of the code.

# Inputs

# Repositories

You will be given two references to pull requests. These could be in the format of a url such as https://github.com/ansible/django-ansible-base/pull/1234 or as ansible/django-ansible-base#1234.

If you do not get two pull request references prompt the user for the two pulls.

# Execution

Your job is to use the gh command to pull the diffs of the two PRs and compare them for equality.

## Step 1: Parse PR References

Extract the repository and PR number from each reference:
- URL format: `https://github.com/ansible/django-ansible-base/pull/1234` → `ansible/django-ansible-base` + `1234`
- Shorthand format: `ansible/django-ansible-base#1234` → `ansible/django-ansible-base` + `1234`

## Step 2: Fetch PR Diffs

Use the GitHub CLI to fetch the diff for each PR (using unique temp files):

```bash
# Create unique temp files
ORIGINAL_DIFF=$(mktemp)
BACKPORT_DIFF=$(mktemp)

# For the original PR
gh pr diff <PR_NUMBER> --repo <OWNER/REPO> > "$ORIGINAL_DIFF"

# For the backport PR
gh pr diff <PR_NUMBER> --repo <OWNER/REPO> > "$BACKPORT_DIFF"
```

## Step 3: Compare the Diffs

Compare the two diffs to check for differences:

```bash
diff -u "$ORIGINAL_DIFF" "$BACKPORT_DIFF"
```

## Step 4: Determine Which PR is the Backport

Check the status of both PRs to identify which one is open (the backport):

```bash
# Check PR status
gh pr view <PR_NUMBER> --repo <OWNER/REPO> --json state,baseRefName
```

The backport PR will typically:
- Have `state: "OPEN"`
- Target a stable/release branch (e.g., `stable-2.4`, `release-1.0`)

The original PR will typically:
- Have `state: "MERGED"` or `state: "CLOSED"`
- Target the main development branch (e.g., `main`, `devel`)

## Step 5: Analyze Results

### If diffs are identical:
- ✅ Report: "Backport is identical to the original PR. No issues found."

### If diffs differ:
Analyze the differences to determine if they are:

**Acceptable differences:**
- Version numbers or release tags
- Branch references (e.g., `main` vs `stable-2.4`)
- Date stamps or timestamps
- Minor whitespace/formatting if pre-commit hooks differ between branches

**Problematic differences:**
- Logic changes
- Missing commits from the original PR
- Additional changes not in the original PR
- Modified functionality

### Report Format:

```markdown
## Backport Review Results

**Original PR**: <repo>#<number>
**Backport PR**: <repo>#<number>

**Status**: [✅ APPROVED | ⚠️ NEEDS REVIEW | ❌ REJECTED]

**Summary**: 
<Brief explanation of findings>

**Differences Found**:
<List any differences with categorization>

**Recommendation**:
<Approve, request changes, or highlight concerns>
```

## Step 6: Check CI Status

Check the status of CI checks on the backport PR:

```bash
gh pr checks <BACKPORT_PR_NUMBER> --repo <OWNER/REPO>
```

Note whether all checks are passing, some are failing, or checks are still pending.

## Step 7: Add Review Comment and Approve (if acceptable)

**Always add a comment in the following standard format:**

### If backport is acceptable AND all CI checks pass:

```bash
gh pr review <BACKPORT_PR_NUMBER> --repo <OWNER/REPO> --approve --body "## Backport Review Complete ✅

**Original PR**: <repo>#<original_number>
**Backport PR**: <repo>#<backport_number>

**Diff Comparison**: Identical / Only acceptable differences found
**CI Status**: All checks passing ✅

**Review Summary**:
- Backport accurately reflects the original PR
- No problematic differences detected
- All CI checks are passing

**Approval**: Approved ✅"
```

### If backport is acceptable BUT CI checks are failing:

```bash
gh pr review <BACKPORT_PR_NUMBER> --repo <OWNER/REPO> --approve --body "## Backport Review Complete ✅ (Conditional)

**Original PR**: <repo>#<original_number>
**Backport PR**: <repo>#<backport_number>

**Diff Comparison**: Identical / Only acceptable differences found
**CI Status**: ⚠️ Some checks are failing

**Review Summary**:
- Backport accurately reflects the original PR
- No problematic differences detected
- ⚠️ CI checks must pass before merge

**Approval**: Conditionally approved - approval is contingent on all CI checks passing before merge.

**Action Required**: Please ensure all CI checks pass before merging."
```

### If backport has problematic differences:

```bash
gh pr review <BACKPORT_PR_NUMBER> --repo <OWNER/REPO> --comment --body "## Backport Review Complete ⚠️

**Original PR**: <repo>#<original_number>
**Backport PR**: <repo>#<backport_number>

**Diff Comparison**: Significant differences detected
**CI Status**: <status>

**Issues Found**:
<List specific problematic differences>

**Recommendation**: Please review the differences and ensure the backport accurately reflects the original PR.

**Action Required**: Address the differences noted above before approval."
```

## Step 8: Cleanup

Remove temporary diff files:

```bash
rm "$ORIGINAL_DIFF" "$BACKPORT_DIFF"
```
