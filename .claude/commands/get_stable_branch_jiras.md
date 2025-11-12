# Get Stable Branch JIRAs

## Preparation

**MANDATORY FIRST STEP:** Before proceeding with any other steps, you MUST:

1. Read `AGENTS_USER.md` in the workspace root
2. Read `CLAUDE.md` in the workspace root
3. Verify you understand:
   - JIRA credentials and comment formatting requirements
   - Git workflow with forked repositories
   - Professional language requirements for commits/JIRA

**DO NOT SKIP THIS STEP.** These files contain critical information about how to interact with JIRA, git remotes, and other systems.

## Argument Processing

We may get up to two arguments.

### Branch

One should be a branch name like stable-x.y where x.y is a major/minor version like 2.6
For the rest of the instructions we will refer to this as {branch}
If the {branch} is not specified, prompt the user for the branch name.
For the rest of the instructions please also refer to {major} and {minor} as extracted from the branch name.

### Repo

The other argument would be a repo name like "django-ansible-base" or "ansible.platform"
For the rest of the instructions we will refer to this value as {repo}

If the {repo} is specified:
    Ensure a directory exists at the root of this repo named exactly the same and that the specified directory is its own git repo.
    If the directory does not exist, give the user a message that the directory behind the repo is missing

If the {repo} is not specified:
    We will use the current directory directly.

For the rest of the instructions we will refer to this directory as {directory}

Once we know which {repo} we are working on we need to determine the remote we will use. 

Look at the list of git remotes and find origin:
- If the origin organization is not "ansible-automation-platform": find the remote that has the organization "ansible-automation-platform" for the same repository
  - Example: if origin is git@github.com:ansible/django-ansible-base.git, find git@github.com:ansible-automation-platform/django-ansible-base.git
  - Example: if origin is https://github.com/john-westcott-iv/aap-gateway, find a remote that points to ansible-automation-platform/aap-gateway
- If the origin org is already "ansible-automation-platform": use origin as the remote
  - Example: if origin is git@github.com:ansible-automation-platform/aap-gateway.git, use that
- If neither case applies or no matching remote is found: prompt the user for clarification on which remote to use

For the rest of the instructions we will refer to this as {remote}

If you can not determine the {directory} prompt the user for clarification.

## Execution

In the {directory} specified.

### Setup
1. Record the current branch name
2. Stash any uncommitted changes (if any exist)

### Analysis
3. Checkout the specified {branch} and hard reset to the same {branch} from the identified {remote}
4. Fetch all tags from the identified {remote} to ensure we have the latest tags locally
5. Find the latest tag matching pattern {major}.{minor}.YYYYMMDD (note: uses dots, not hyphens)
   - Use command: `git tag -l "{major}.{minor}.*" | sort -V | tail -1`
6. Get all commits since that tag (git log <tag>..HEAD --oneline --no-merges)
7. For each commit:
   - Use `gh pr list --search <commit_hash> --state merged` to find which PR in the {remote} repo contains this commit
     - DO NOT extract PR numbers from commit messages - those may reference PRs from a different repo (e.g., upstream)
     - We need the backport PR number from {remote}, not the original PR number
   - Get PR title from the identified PR
   - Extract first AAP-\d+ pattern from PR title
   - Query JIRA for that issue's fields:
     - **Important:** When using `mcp_atlasian_jira_get_issue`, request all fields:
       - Use `fields: "*all"` to get all fields including custom fields
       - The Target Version field is `customfield_12319940` and contains an array of version strings
     - Extract the following fields from the JIRA response:
       - `summary`: The JIRA title
       - `customfield_12319940`: The "Target Version" field (array of version strings)
       - `customfield_12320850`: The "Release Note Type" field
       - `customfield_12317313`: The "Release Note" field
     - For the "Missing Data" column, check:
       - If `customfield_12320850` (Release Note Type) is not populated: report "Release Note Type missing"
       - If `customfield_12320850` is populated but NOT "Release Note Not Required":
         - Check if `customfield_12317313` (Release Note) is empty
         - If empty, report "Release Note missing"
       - If both are properly populated, report "None"
8. Output a markdown table with columns: Commit Hash | PR | JIRA | JIRA Title | Target Version | Missing Data
   - Commit Hash column: link to the commit in {remote} (e.g., https://github.com/ansible-automation-platform/repo-name/commit/{hash})
   - PR column: link to the PR in {remote}
   - JIRA column: link to https://issues.redhat.com/browse/{key}
   - JIRA Title column: the summary field from JIRA
   - Target Version: comma-separated list of versions from `customfield_12319940`, or "None"
   - Missing Data: report any missing Release Note Type or Release Note fields, or "None" if all required fields are populated
   - For commits without PR/JIRA, use "N/A"

### Cleanup
9. Checkout the original branch recorded in step 1
10. Pop the stash if one was created in step 2

Before outputting the table, print: "Here are the commits and their JIRAs since {tag}:" (where {tag} is the actual tag found in step 5).
Then output only the table, no additional summaries.

