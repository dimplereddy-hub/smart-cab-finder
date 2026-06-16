# GitLab Compliance Checker

A Streamlit-based tool that analyses GitLab project repositories and produces a detailed compliance report covering documentation, tooling, security, CI/CD, and coding standards.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Compliance Score](#compliance-score)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Docker](#docker)
- [Testing](#testing)
- [Documentation](#documentation)
- [License](#license)

---

## Features

### Single Project Analysis

Enter any GitLab project URL or ID, select a branch, and receive a full compliance report:

| Category | What is checked |
|---|---|
| **Compliance Score** | 8-point weighted score (linter, type checker, secret scanning, dependency audit, coverage, changelog, pre-commit, CI) |
| **Documentation Files** | README.md, CONTRIBUTING.md, USER_MANUAL.md, AGENTS.md |
| **Repository Health Files** | .gitignore, .editorconfig, CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md, .env.example, Dockerfile, .dockerignore |
| **Quality & Tools** | Ruff, Mypy, Vulture, Bandit, Pylint, Flake8, ESLint, Biome, Prettier, Knip, and more |
| **Security** | Secret scanning (Gitleaks / TruffleHog), dependency audit (pip-audit / npm audit / snyk), SAST |
| **Testing** | pytest / jest / vitest, coverage reporting, enforced thresholds |
| **Automation & CI** | GitLab CI pipeline, pre-commit hooks, git-cliff changelog automation |
| **CI Pipeline Analysis** | Stage-by-stage breakdown (test, lint, format, type_check, coverage) with detected tools |
| **Pre-commit Hook Analysis** | Per-category hook detection (lint, format, type_check, security, quality) |
| **Metadata** | Project description and Git tags |
| **License** | AGPLv3 compliance |
| **Issue / MR Templates** | GitLab issue and merge request template presence |
| **Actionable Suggestions** | Specific fix instructions for every failed check |

### Batch Project Analysis

- Enter multiple project URLs — one per line
- Choose a single branch applied to all projects; automatically falls back to each project's default branch if not found
- Each project renders as a bordered card showing score, stack, and key metric badges
- Click any card to expand the full compliance report (identical to single project view)

---

## How It Works

```
User enters project URL + branch
        │
        ▼
  GitLab API: GET /projects/{id}
        │
        ▼
  run_project_compliance_checks()
  ├── check_readme()          → README presence and section quality
  ├── check_license()         → AGPLv3 LICENSE file validation
  ├── check_templates()       → .gitlab/ issue & MR templates
  ├── check_metadata()        → description and Git tags
  ├── check_tools()           → language detection + config file scanning
  │     └── detect_project_type()  → probes pyproject.toml / package.json
  ├── check_docs()            → README.md, CONTRIBUTING.md, USER_MANUAL.md, AGENTS.md
  ├── check_repo_files()      → .gitignore, Dockerfile, SECURITY.md, etc.
  ├── check_ci_pipeline()     → parses .gitlab-ci.yml stage by stage
  └── check_precommit()       → parses .pre-commit-config.yaml hook by hook
        │
        ▼
  render_project_compliance_details(report)
```

---

## Compliance Score

The score is a percentage of **8 binary checks** — each either passes (✅) or fails (❌):

| # | Check | What it looks for |
|---|---|---|
| 1 | **Linter** | ruff / biome / eslint in config files or CI |
| 2 | **Type Checker** | mypy / knip |
| 3 | **Secret Scanning** | gitleaks / trufflehog / detect-secrets in CI or pre-commit |
| 4 | **Dependency Audit** | pip-audit / npm audit / snyk / uv audit |
| 5 | **Coverage Reporting** | pytest-cov / --cov flag / codecov |
| 6 | **Changelog Automation** | cliff.toml present or git-cliff in CI |
| 7 | **Pre-commit Hooks** | .pre-commit-config.yaml present |
| 8 | **GitLab CI Pipeline** | .gitlab-ci.yml present |

**Score = (checks passed / 8) × 100**

The Score Breakdown expander in the report shows exactly which checks passed or failed and why.

---

## Project Structure

```
gitlab-compliance-checker/
├── app.py                              # Streamlit entry point
├── docker-compose.yml                  # Docker Compose configuration
├── Dockerfile                          # Multi-stage Docker build
├── entrypoint.sh                       # Container startup script
├── pyproject.toml                      # Project metadata and dependencies
├── src/
│   └── gitlab_compliance_checker/
│       ├── infrastructure/
│       │   └── gitlab/
│       │       ├── client.py           # Async GitLab API client (glabflow)
│       │       ├── api_helper.py       # Branch listing
│       │       ├── parsers.py          # YAML / JSON parsing
│       │       ├── pipeline_checker.py # CI pipeline & pre-commit analysis
│       │       └── projects.py         # Project lookup utilities
│       ├── services/
│       │   └── compliance/
│       │       ├── compliance_service.py   # Main orchestrator + suggestions
│       │       ├── docs_checker.py         # Doc & repo health file checks
│       │       ├── file_classifier.py      # File extension classification
│       │       ├── license_checker.py      # AGPLv3 validation
│       │       ├── metadata_checker.py     # Description & tags
│       │       ├── project_detector.py     # Language detection
│       │       ├── readme_checker.py       # README quality analysis
│       │       ├── templates_checker.py    # Issue / MR template detection
│       │       └── tools_checker.py        # Tool detection across config files
│       └── ui/
│           ├── compliance.py           # All UI rendering (single + batch)
│           └── main.py                 # Sidebar config, client init
├── tests/                              # pytest test suite
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_client.py
│   ├── test_modes_compliance_mode.py
│   ├── test_project_detector.py
│   ├── test_project_ui.py
│   └── test_gitlab_utils/
│       ├── test_pipeline_checker.py
│       └── test_pipeline_checker_advanced.py
├── README.md
├── CONTRIBUTING.md
├── USER_MANUAL.md
├── AGENTS.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
└── LICENSE
```

---

## Requirements

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
- GitLab Personal Access Token with `read_api` scope (minimum)

---

## Installation

### Using uv (recommended)

```bash
git clone https://code.swecha.org/tools/gitlab-compliance-checker.git
cd gitlab-compliance-checker
uv sync
```

### Using pip

```bash
git clone https://code.swecha.org/tools/gitlab-compliance-checker.git
cd gitlab-compliance-checker
python3 -m venv .venv && source .venv/bin/activate
pip install .
```

---

## Configuration

Create a `.env` file in the project root (never commit this file):

```env
GITLAB_URL=https://code.swecha.org
GITLAB_TOKEN=your_personal_access_token
```

### Creating a GitLab Personal Access Token

1. GitLab → **User Settings → Access Tokens**
2. Name: `compliance-checker` — Scope: `read_api`
3. Set an expiry date, click **Create personal access token**
4. Copy the token immediately — GitLab shows it only once
5. Paste it into `.env`

> `.env` is listed in `.gitignore` — your token will not be committed.

---

## Running the App

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser. Enter your GitLab URL and token in the sidebar if you did not create a `.env` file.

---

## Docker

### Docker Compose (recommended)

```bash
# 1. Create .env with your credentials
cp .env.example .env   # then edit with your values

# 2. Build and start
docker compose up --build

# 3. Open http://localhost:8501

# Stop
docker compose down
```

### Docker (manual)

```bash
docker build -t gitlab-compliance-checker .

docker run --rm -p 8501:8501 \
  -e GITLAB_URL="https://code.swecha.org" \
  -e GITLAB_TOKEN="your_token" \
  gitlab-compliance-checker
```

---

## Testing

```bash
uv run pytest                            # full suite
uv run pytest -v                         # verbose output
uv run pytest -x                         # stop on first failure
uv run pytest --cov --cov-report=term-missing   # with coverage
uv run pytest tests/test_pipeline_checker.py    # single file
```

---

## Documentation

| Document | Description |
|---|---|
| [USER_MANUAL.md](USER_MANUAL.md) | Step-by-step usage guide for end users |
| [AGENTS.md](AGENTS.md) | AI agent context — architecture, conventions, data flow |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute code, report issues, run checks |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |

---

## License

This project is licensed under the **GNU Affero General Public License v3.0**.
See [LICENSE](LICENSE) for the full text.
