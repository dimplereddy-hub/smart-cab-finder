# Contributing to GitLab Compliance Checker

Thank you for contributing! This document covers how to report issues, suggest features, and submit code.

## Reporting Issues

- Search existing issues before opening a new one.
- Use the provided issue templates in `.gitlab/issue_templates/`.
- Include: reproduction steps, Python version, OS, and any relevant logs or screenshots.

## Suggesting Features

- Open an issue labelled `feature-request`.
- Describe the feature, its intended usage, and why it improves compliance checking.

## Code Contributions

- Fork the repository and create a branch from `main`.
- Follow [PEP 8](https://pep8.org/) and the existing code style.
- Write [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation only
  - `refactor:` code change with no behaviour change
  - `test:` adding or fixing tests
  - `chore:` tooling / maintenance
- Add or update tests for every change.
- Run the full quality suite before submitting a merge request.

## Local Development Setup

### Install dependencies

```bash
uv sync --all-extras
```

### Install pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

### Run hooks manually

```bash
uv run pre-commit run --all-files   # all files
uv run pre-commit run               # staged files only
```

### Individual tool commands

| Tool | Command |
|---|---|
| **Ruff (lint)** | `uv run ruff check .` |
| **Ruff (format)** | `uv run ruff format .` |
| **Mypy** | `uv run mypy --config-file mypy.ini .` |
| **Vulture** | `uv run vulture src/ --min-confidence 80` |
| **Bandit** | `uv run bandit -r src/` |
| **UV Audit** | `uv audit` |

### Running tests

| Command | Purpose |
|---|---|
| `uv run pytest` | Full test suite |
| `uv run pytest -v` | Verbose output |
| `uv run pytest -x` | Stop on first failure |
| `uv run pytest --cov --cov-report=term-missing` | With coverage |
| `uv run pytest tests/test_app.py` | Single file |

## Merge Request Process

- Target the `main` branch.
- Use the provided MR templates in `.gitlab/merge_request_templates/`.
- Fill in: description of changes, related issues (`Closes #N`), type of change, test status.
- All CI checks must pass before merge.
- Respond to review feedback promptly.

## Code of Conduct

Please read and follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

Thank you for helping improve GitLab Compliance Checker!
