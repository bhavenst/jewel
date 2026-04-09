# Contributing to aap-gateway

Everybody is welcome to contribute to AAP Gateway and this guide is here to explain how to make the contributions and collaborate with code maintainers in order to see those contributions accepted to the code base.

## Getting started

To get started with this repo, review the documentation at the following links:

[Readme - Starting gateway](./README.md#starting-gateway)

[Docs - Gateway Development](./docs/development/development-gateway.md)

## Making contributions

Before making your pull request (PR) to this repository, read through following sections to understand the expectations and responsibilities.

### Expectations & Responsibilities

These are expectations you need to be aware even **before** you start contributing to the project.

**For contributors:**

- **Single focus**
  - Make your PR focus on one issue/bug/feature. Do not bunch up a few ideas together
- **Reasonable size**
  - Smaller PRs are easier to review and quicker to get merged. Simple as that.
  - Ideal size is **up to 15** files changed.
- **Split up large contributions**
  - Start development early (in the cycle of a release) and create several smaller PRs.
  - If you have multiple PRs for a larger change, make sure to mention in the description that a PR is part N of that larger change,
  - If you implement a whole feature and hit this repo with a PR containing over 50 files in the last sprint before release, you will be disappointed.
- **Well described/documented changes**
  - Include a complete description of the change in the PR (more on this in Pull Request section below)
  - Fill out the PR template, really, it is there for a reason (even if using `gh` CLI)
  - If the PR should not be immediately merged when approved, then add `[WIP]` or ensure it is in a Draft state
- **Respond to review comments**
  - Opening a PR means starting a conversation, keep it alive
  - Make your acknowledgment of a review comment visible with an explicit comment of what will or won't be done, even if all you can say now is "Will look into it" 
  - Avoid responding with only emojis, as these can be interpreted in multiple ways
  - Add new commits when addressing review comments, don't rebase/squash commits. This ensures that the incremental changes are clearly visible
- **Close open conversations**
  - Close any conversations that have been addressed.

**For maintainers/reviewers:**

- **Review response times**
  - Maintainers of this repo will make a reasonable effort to start reviewing the PRs within 2 business days (most likely earlier)
  - Keep re-reviewing as new commits are added on daily basis
- **Provide full review**
  - Maintainers will aim to review a PR in its entirety or leave a comment if they have a good reason to re-review the PR at a later point
- **Label the PR properly**
  - Maintainers will use labels to indicate their view of the PR state. These might include:
    - Size: "Small", "Medium", "Large", "X-Large" (hopefully not the last one)
    - State: "Triage", "Ready for review", "Needs info", "Failing CI", "Stale", etc.
    - Priority: "Critical", "Normal", "Low"
  - The labels should always provide current state of the PR without having to read all comments
- **Close open conversations**
  - Any conversations that have been addressed should be closed
- **Merge approved PRs**
  - PRs will be merged once it gets 2 approvals
- **Squash commits when merging**
  - Squashing commits makes for clean history, unless the individual commits are necessary.
- **Close old PRs**
  - PRs will get a label "Stale" after 2 weeks of inactivity. This label will be removed once the conversation is restarted.
  - PRs will be closed if there is no activity 2 weeks after labeling it stale.
  - This process is manual at this time but will be automated in the future.

### Pull Requests

This section provides instructions on creating the pull requests.

#### Pre-commit hooks

This repository uses git hooks to catch linter issues locally before they reach CI. If you are launching a local Gateway instance using aap-dev, then these will need to be explicitly configured:

```shell
$> make git_hooks_config
```

This make target is a dependency of `make docker-compose`, which is used to launch a local instance directly from this repository. In this case, the above command is not required.

#### Pull request structure

When opening a PR on Github web UI, you'll be presented with a PR template with sections and checklists to help you provide necessary information for the reviewers. This includes the change description, testing instructions, and any required follow-up actions.

This template **must** be completed in its entirety for a review to begin.

**Note:** If using the `gh` tool to submit a PR the template is optional, but strongly recommended.
The reviewers will ask questions that are already provided by the template if it is not included.

The following are of particular note:

- **PR title**
  - The title is expected to contain a relevant Jira Issue at the beginning of the concise description. For instance:

    ```text
    [AAP-12345] One-sentence summary of changes
    ```

- **High level description**
  - To help you describe the change, the template starts with the three important questions about the proposed changes: **what**, **why** and **how**. Ensure that these are questions are addressed at a high level first, then add more details if needed.

- **References and related content**
  - If your PR is related to an SDP or a PR in a separate repo, such as django-ansible-base, provide links to these
  references in the description body. This allows reviewers to quickly gain context on the proposed changes.

- **Testing instructions**
  - The PR must contain detailed instructions on how to test your changes in a local instance. Ideally, these are step by step instructions to
  both confirm the change is effective and showcase the original behavior.
  - If the PR does not make any functional changes, then clearly indicate how the change from the PR can be examined.
  - No testing instructions? Not even an explanation why not? No reviews. Simple as that.

- **Code expectations**
  - Read and follow the self-review checklist. This ensures that you are aware of ramifications (such as performance,
  documentation, security, etc.) that may result from your change.
  - Follow coding best practices (DRY, KISS, SOLID, etc.)

#### Backporting to stable release branches

It is the PR owner's responsibility to ensure changes are backported where needed. Backporting for this repository is managed via Patchback.

**Creating a backport PR:**

- To backport using Patchback, specific labels are added to your PR targeting the devel branch. There is no limit to the number of labels you can add,
just add them for every version you want to backport to. Note the `-` in the label - there may be multiple, similar, labels, and
these must exactly match for Patchback to function.
  - `backport-2.5` for stable-2.5 backports
  - `backport-2.6` for stable-2.6 backports
  - `backport-2.7` for stable-2.7 backports
- Once the PR is merged, Patchback will create a PR. This will work even if the PR is already merged.
- After the backport PR is automatically created, modify the PR title to include the Jira issue number of the backport. In the
following string, only `[AAP-23456]` was manually added:

  ```text
  [AAP-23456][PR #954/a8575cd1 backport][stable-2.6][AAP-12345] $TITLE
  ```
