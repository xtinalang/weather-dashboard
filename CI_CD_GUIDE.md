# CI/CD Pipeline Guide

This guide explains how to use the CI/CD pipeline for the weather dashboard project with separate development and production branches.

## Overview

The CI/CD pipeline is designed to enforce code quality standards and ensure that anyone working on the project uses the same linting and testing tools defined in `pyproject.toml`.

## Branch Structure

### Development Branch (`develop`/`dev`/`development`)
- **Purpose**: Feature development and testing
- **CI Workflow**: `ci-dev.yml`
- **Checks**: Basic linting, testing, and code quality
- **Coverage**: Reports generated but not enforced

### Production Branch (`main`/`master`/`production`)
- **Purpose**: Production-ready code
- **CI Workflow**: `ci-prod.yml`
- **Checks**: Strict linting, testing, security scans, and integration tests
- **Coverage**: Enforced minimum 80% coverage
- **Deployment**: Automatic staging deployment on successful merge

## Workflow Files

### 1. `ci-dev.yml` - Development CI
- **Triggers**: Push/PR to development branches
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Jobs**:
  - `test`: Runs linting (ruff, flake8, mypy) and tests
  - `security-scan`: Basic security checks
  - `code-quality`: Coverage reports and complexity analysis
  - `pre-commit`: Pre-commit hook validation

### 2. `ci-prod.yml` - Production CI
- **Triggers**: Push/PR to production branches
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Jobs**:
  - `test`: Strict linting and testing with coverage enforcement
  - `security-scan`: Comprehensive security scanning
  - `build-and-test`: Package building and installation testing
  - `integration-tests`: Full integration testing with PostgreSQL
  - `docker-build`: Docker image building and testing
  - `deploy-staging`: Automatic staging deployment
  - `notify`: Deployment status notifications

### 3. `branch-protection.yml` - Branch Protection
- **Triggers**: All PRs to protected branches
- **Jobs**:
  - `enforce-quality`: Quality checks and dependency validation
  - `size-check`: PR size analysis and warnings
  - `dependency-check`: Security vulnerability scanning

### 4. `publish.yml` - Package Publishing
- **Triggers**: Git tags and releases
- **Jobs**:
  - `quality-checks`: Pre-publish quality validation
  - `build-and-publish`: Package building and publishing

## Dependencies and Tools Used

The pipeline uses the exact dependencies and configurations defined in your `pyproject.toml`:

### Linting Tools
- **Ruff**: Fast Python linter and formatter
- **Flake8**: Python code style checker
- **MyPy**: Static type checker

### Testing Tools
- **Pytest**: Testing framework
- **Coverage**: Code coverage measurement
- **Pytest-playwright**: Browser automation testing

### Security Tools
- **Safety**: Dependency vulnerability scanner
- **Bandit**: Security linter for Python code

### Development Tools
- **Pre-commit**: Git hooks for code quality
- **UV**: Fast Python package manager

## Setting Up Your Development Environment

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync --dev
   uv pip install -e .
   ```

3. **Install pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

## Running Quality Checks Locally

Before pushing code, run the same checks that CI will run:

### Linting
```bash
# Ruff linting
uv run ruff check .
uv run ruff format --check .

# Flake8
uv run flake8 .

# MyPy
uv run mypy weather_app/
```

### Testing
```bash
# Run tests
uv run pytest --verbose

# Run tests with coverage
uv run coverage run -m pytest
uv run coverage report
uv run coverage html
```

### Security Scanning
```bash
# Dependency vulnerabilities
uv add safety --dev
uv run safety check

# Code security issues
uv add bandit --dev
uv run bandit -r weather_app/
```

### Pre-commit Hooks
```bash
# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Workflow Process

### For Development Work
1. Create feature branch from `develop`
2. Make changes and commit
3. Push to feature branch
4. Create PR to `develop`
5. CI runs development checks
6. Review and merge

### For Production Releases
1. Create PR from `develop` to `main`
2. CI runs comprehensive production checks
3. Review and merge
4. Automatic deployment to staging
5. Manual promotion to production

## Branch Protection Rules

The pipeline enforces these rules:
- All PRs must pass CI checks
- Dependencies must be locked (`uv.lock` up to date)
- No large files (>100MB)
- Basic security checks pass
- Code quality standards met

## Environment Variables and Secrets

### Required Secrets
- `PYPI_SECRET`: PyPI token for package publishing

### Optional Secrets
- `CODECOV_TOKEN`: For code coverage reporting
- Database credentials for integration tests
- Deployment credentials for staging/production

## Customization

### Adding New Checks
1. Add new tools to `pyproject.toml` dev dependencies
2. Update workflow files to include new checks
3. Test locally before pushing

### Modifying Branch Names
Update the branch names in workflow files:
- `ci-dev.yml`: Line 4-5 (development branches)
- `ci-prod.yml`: Line 4-5 (production branches)
- `branch-protection.yml`: Line 4 (all protected branches)

### Changing Coverage Requirements
Update `ci-prod.yml` line with `--fail-under=80` to your desired coverage percentage.

## Troubleshooting

### Common Issues
1. **UV lock file out of date**: Run `uv lock` to update
2. **MyPy errors**: Check type annotations and imports
3. **Coverage too low**: Add more tests or adjust threshold
4. **Security vulnerabilities**: Update dependencies with `uv add package@latest`

### Getting Help
- Check workflow logs in GitHub Actions tab
- Run checks locally to debug issues
- Review `pyproject.toml` configuration

## Best Practices

1. **Commit Messages**: Use conventional commits format
2. **PR Size**: Keep PRs small and focused
3. **Testing**: Write tests for new features
4. **Dependencies**: Keep dependencies updated
5. **Security**: Never commit secrets or API keys

## Monitoring and Notifications

The pipeline provides:
- ✅ Success notifications for all checks
- ❌ Failure notifications with details
- 📊 Coverage reports and statistics
- 🔒 Security vulnerability reports
- 📦 Build artifacts for debugging
