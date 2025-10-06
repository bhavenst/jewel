# AGENTS.md

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

## Security Considerations

- **Coverage Requirement**: SonarCloud requires 80% code coverage for quality gates
- **Service Authentication**: All services use JWT token authentication
- **Secrets Management**: Never commit secrets - use `container-startup.yml` for local dev config
- **Pre-commit Hooks**: Always run to catch security and quality issues

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

## Additional Resources

For user-specific preferences and instructions, check `AGENTS_USER.md` if it exists in the repository.
