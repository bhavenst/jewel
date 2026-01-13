# Tagging the gateway repo

## Inputs

### Tag
You will get a tag name like 2.6.20251119

The tag must be in the format {major}.{minor}.{date} where date is in the format YYYYMMDD.

If not provided, please prompt the user for the tag name.

Lets refer to this as {tag}

### Hash
Optionally you will be provided with a commit hash.

Lets refer to this as {commit}

## Preparation

**MANDATORY FIRST STEP:** Before proceeding with any other steps, you MUST:

1. Read `AGENTS_USER.md` in the workspace root
2. Read `AGENTS.md` in the workspace root
3. Verify you understand:
   - JIRA credentials and comment formatting requirements
   - Git workflow with forked repositories
   - Professional language requirements for commits/JIRA

**DO NOT SKIP THIS STEP.** These files contain critical information about how to interact with JIRA, git remotes, and other systems.

Ensure the user has already run the command get_stable_branch_jiras so that they know what is going into the release. If its not yet been run in the session check with the user to see if they need you to run that command first.

## Execution

Look at the list of git remotes using:
```
git remote -v
```

Find the appropriate remote:
- If the origin organization is not "ansible-automation-platform": find the remote that has the organization "ansible-automation-platform" for the same repository
  - Example: if origin is git@github.com:ansible/django-ansible-base.git, find git@github.com:ansible-automation-platform/django-ansible-base.git
  - Example: if origin is https://github.com/john-westcott-iv/aap-gateway, find a remote that points to ansible-automation-platform/aap-gateway
- If the origin org is already "ansible-automation-platform": use origin as the remote
  - Example: if origin is git@github.com:ansible-automation-platform/aap-gateway.git, use that
- If neither case applies or no matching remote is found: prompt the user for clarification on which remote to use

Let's refer to this remote name as {remote}

The branch we will be working with on the remote will have the name stable-{major}.{minor} where {major} and {minor} come from the supplied {tag}. Let's refer to this as {branch}

Fetch the latest version of the branch:
```
git fetch {remote} {branch}
```

If {commit} was not passed in, we need to get the latest commit from {remote}/{branch} and set {commit} to this value. Use git log to find this:
```
git log {remote}/{branch} -1 --format=%H
```

Create an annotated tag against the branch at {commit} with the command:
```
git tag -a {tag} {commit} -m {tag}
```

Verify the tag was created successfully:
```
git show {tag}
```

Then push the tag to the {remote}:
```
git push {remote} {tag}
```