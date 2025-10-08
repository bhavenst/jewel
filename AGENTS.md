# AGENTS.md

## Getting Started - Required Reading

**Before proceeding with any work, please read these files in order:**

1. **README.md** - Project overview and setup instructions
2. **TESTING.md** - Testing guidelines and procedures
3. **AGENTS_USER.md** - User-specific preferences (if it exists)
4. **django-ansible-base/README.md** - Information about the shared library (if it exists)

## Project Overview

AAP Services Gateway provides a single entry point that sits in front of all services within Ansible Automation Platform (AAP). The gateway handles authentication, authorization, and proxying for Controller, Hub, EDA, and Lightspeed services.

**Key Technologies:**
- Django REST Framework
- Envoy proxy
- Redis cache
- PostgreSQL database
- pytest for testing

**Related Repositories:**
- This repo may have a checkout of `django-ansible-base` as a git submodule - it's a separate git repo with its own tests and configuration
- `django-ansible-base` is a library used by this project to provide additional functionality which is common across all of ansible-automation-platform

## Build and Test Commands

### Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements/requirements_dev.txt

# Generate proxy configuration (optional)
make tools/generated/proxy.yml

# Start development environment
docker login quay.io
make docker-compose
```

### Running Tests
**CRITICAL:** Always use `tox` instead of `pytest` directly. Direct pytest will fail with Django configuration errors.

```bash
# Run all tests (parallel by default)
tox -e 311

# Run single-threaded (for debugging)
PYTEST_NUM_PROCESSES=1 tox -e 311

# Run specific tests
tox -e 311 -- -k "test_pattern_name" -v
tox -e 311 -- aap_gateway_api/tests/path/to/test_file.py -v

# Stress test for threading issues
./run_tox_batch.sh
```

### django-ansible-base Tests
```bash
cd django-ansible-base
tox -e 311
```

## Code Style Guidelines

**Pre-commit Hooks** (enforced automatically):
- **black**: Code formatting
- **flake8**: Linting  
- **isort**: Import sorting

**Testing Conventions:**
- Always use parameterized tests (`@pytest.mark.parametrize`) when writing multiple similar test cases
- Place tests in appropriate subdirectory under `aap_gateway_api/tests/`
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Please read the `TESTING.md` file for more details about testing

## Security Considerations

- **Coverage Requirement**: SonarCloud requires 80% code coverage for quality gates
- **Service Authentication**: All services use JWT token authentication
- **Secrets Management**: Never commit secrets - use `container-startup.yml` for local dev config
- **Pre-commit Hooks**: Always run to catch security and quality issues

### GitHub Actions Security
- **NEVER use user-controlled data directly in run blocks**
  → Always pass through environment variables (e.g., `github.event.pull_request.body`)
- **Bad:** `echo "${{ github.event.pull_request.body }}" > file.txt`
- **Good:** Use env block and reference variables:
  ```yaml
  env:
    PR_BODY: ${{ github.event.pull_request.body }}
  run: |
    printf '%s' "$PR_BODY" > file.txt
  ```
- GitHub Actions sanitizes environment variables before passing to shell
- This prevents command injection vulnerabilities

## Architecture & Patterns

### Parallel Test Execution
- Tests run with pytest-xdist across multiple workers by default
- All fixtures designed for worker isolation (cache, preferences, JWT keys)
- Port allocation uses worker-specific offsets to prevent conflicts
- Database isolation via separate test DB files per worker

### Key Components
- **WorkerIsolatedRedisCache**: Custom cache backend for parallel test safety
- **preference_manager fixture**: Context manager for preference isolation
- **ensure_jwt_keys fixture**: JWT authentication for service tests
- **Service fixtures**: Auto-depend on JWT keys for authentication

### Git Workflow Patterns
- Squash related commits into logical units
- Use `git commit --amend` for iterative fixes
- Professional commit messages despite colorful conversation
- Always give Claude co-author credit in commits

### Pull Request Guidelines
- **ALWAYS check for PR templates** in both the aap-gateway repo and django-ansible-base repo
  - Look for `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE.md`
  - Follow the template structure if one exists
- **PR titles MUST be prefixed with JIRA number**: `[AAP-1234] Description of changes`
  - If JIRA number is not known, **STOP and prompt the user** for the JIRA ticket number
  - Never create a PR without the JIRA prefix

### Common Gotchas
- Service tests failing with "Authentication credentials were not provided"
  → Missing `ensure_jwt_keys` dependency on service fixture
- Intermittent test failures → Usually cache/preference isolation issues
- Import errors for missing modules → Check for stray test files

### Debugging Methodology
- Always investigate root causes of threading/parallel test issues
- Stress test fixes with batch runs (`tools/scripts/run_tox_batch.sh`)
- Prefer systematic debugging over quick hacks
- Use single-threaded runs to isolate threading problems

## JIRA Ticket Creation

When using MCP JIRA tools to create and update tickets programmatically:

### Workstream Custom Field
The **Workstream** field is a custom field that requires special handling:
- Field ID: `customfield_12319275`
- Type: Multi-select (array of options)
- Use `mcp_atlasian_jira_search_fields` with keyword "workstream" to find field details

### Creating Issues with Workstream
**Important:** Workstream cannot be set during the `create_issue` call and must be updated after creation:

```python
# Step 1: Create the issue
mcp_atlasian_jira_create_issue(
    project_key="AAP",
    summary="Your summary",
    issue_type="Story",
    description="Your description",
    components="cicd"
)

# Step 2: Add Workstream after creation
mcp_atlasian_jira_update_issue(
    issue_key="AAP-12345",
    fields={},
    additional_fields={
        "customfield_12319275": [{"value": "Installers and Productization"}]
    }
)
```

**Common Workstream Values:**
- "Installers and Productization"
- "UI/UX"
- "API Development"

**Tip:** Always use `mcp_atlasian_jira_search_fields` to discover custom field IDs when needed.

## Additional Resources

For user-specific preferences and instructions, check `AGENTS_USER.md` if it exists in the repository.
