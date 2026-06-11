# AGENTS.md — GitLab Compliance Checker

This file describes the AI agent context for this repository: its purpose, architecture, conventions, and how an AI agent should navigate and modify it.

## Project Purpose

GitLab Compliance Checker is a Streamlit web application that analyses GitLab project repositories and produces compliance reports. It checks documentation, tooling, security, CI/CD configuration, and coding standards, then scores the project and generates actionable suggestions.

It is **not** a user analytics tool, leaderboard, or MR/issue scoring system. All code that does not serve compliance checking is out of scope.

## Architecture

```
app.py                              → Streamlit entrypoint, calls ui.main.main()

src/gitlab_compliance_checker/
  infrastructure/gitlab/
    client.py                       → Async GitLab API client (glabflow-based)
                                      Public API: _get(), _get_paginated(), _request()
    api_helper.py                   → get_project_branches()
    parsers.py                      → parse_yaml(), parse_json()
    pipeline_checker.py             → check_ci_pipeline(), check_precommit()
                                      EXPECTED_STAGES, STAGE_TOOLS, PRECOMMIT_CATEGORIES
    projects.py                     → extract_path_from_url(), get_project_with_retries()

  services/compliance/
    compliance_service.py           → run_project_compliance_checks() — main orchestrator
                                      get_dx_suggestions() — generates actionable suggestions
    docs_checker.py                 → check_docs(), check_repo_files()
                                      REQUIRED_DOCS, REQUIRED_REPO_FILES
    file_classifier.py              → classify_files()
    license_checker.py              → check_license()
    metadata_checker.py             → check_metadata()
    project_detector.py             → detect_project_type()
    readme_checker.py               → check_readme()
    templates_checker.py            → check_templates()
    tools_checker.py                → check_tools() — language detection + config file scanning

  ui/
    compliance.py                   → All UI rendering:
                                      render_project_compliance_details()
                                      render_compliance_mode()
                                      render_batch_project_compliance_internal()
                                      render_dx_ci_pipeline_ui()
                                      render_precommit_analysis_ui()
    main.py                         → Streamlit sidebar config, GitLabClient init, calls render_compliance_mode()
```

## Data Flow

```
User enters project URL + branch
  → extract_path_from_url() → project ID
  → GitLabClient._get("/projects/{id}") → project info
  → run_project_compliance_checks()
      ├── check_readme()        → GET /repository/files/README.md
      ├── check_license()       → GET /repository/files/LICENSE
      ├── check_templates()     → GET /repository/tree/.gitlab/
      ├── check_metadata()      → GET /projects/{id}
      ├── classify_files()      → GET /repository/tree
      ├── check_tools()         → probes config files directly (_get)
      │     → detect language from pyproject.toml / package.json presence
      │     → fetch .gitlab-ci.yml, .pre-commit-config.yaml, pyproject.toml, etc.
      │     → scan text for tool names
      │     → calculate dx_score (8 binary checks)
      ├── check_docs()          → GET /repository/files/{doc} for each required doc
      ├── check_repo_files()    → GET /repository/files/{file} for each health file
      ├── check_ci_pipeline()   → parses .gitlab-ci.yml YAML
      └── check_precommit()     → parses .pre-commit-config.yaml YAML
  → render_project_compliance_details(report)
```

## Key Conventions

### Adding a new compliance check

1. Create or extend a checker in `services/compliance/`
2. Import and call it in `compliance_service.run_project_compliance_checks()`
3. Add the result key to the returned dict
4. Add display logic in `ui/compliance.render_project_compliance_details()`
5. Optionally add suggestions in `compliance_service.get_dx_suggestions()`

### Adding new tools to detect

- **CI pipeline tools**: add to `STAGE_TOOLS` in `pipeline_checker.py`
- **Pre-commit tools**: add to `PRECOMMIT_CATEGORIES` in `pipeline_checker.py`
- **Config-file tools**: add to `check_tools()` in `tools_checker.py`

### Language detection

`tools_checker.check_tools()` detects project language by directly probing config files via `_get()` (not tree listing — that was unreliable). If nothing found at root, it fetches the root tree once and probes one subdirectory level.

### GitLab API calls

Always use `gl._get(endpoint, params=dict)` or `gl._get_paginated(endpoint, params=dict)`. Never pass `path` as a key inside `params` to `_get_paginated` — it conflicts with glabflow internals.

### Stage name normalisation

CI stage names with hyphens (e.g. `type-check`) are normalised to underscores (`type_check`) in `pipeline_checker.py` to match `EXPECTED_STAGES`.

### Tool matching

- Word tools (e.g. `ruff`, `mypy`): matched with `\bword\b` regex
- Flag-style tools (e.g. `--cov`): matched with plain substring since `\b` does not work before `-`

## Compliance Score

The score (`dx_score`) is calculated in `tools_checker.check_tools()`:

```python
checks = [
    linter present?,        # ruff / biome / eslint
    type_checker present?,  # mypy / knip
    secret_scanning?,       # gitleaks / trufflehog / detect-secrets
    dependency_audit?,      # pip-audit / npm audit / snyk
    coverage?,              # pytest-cov / --cov
    git_cliff?,             # cliff.toml / git-cliff in CI
    pre_commit?,            # .pre-commit-config.yaml
    gitlab_ci?,             # .gitlab-ci.yml
]
score = (passed / 8) * 100
```

## Test Suite

```
tests/
  conftest.py                          → FakeStreamlitModule, make_fake_st(), autouse fixtures
  test_app.py                          → main() routing (no-token, client error, compliance mode)
  test_client.py                       → GitLabClient async API methods
  test_modes_compliance_mode.py        → render_compliance_mode(), render_batch_*()
  test_project_detector.py             → detect_project_type()
  test_project_ui.py                   → render_project_compliance_details()
  test_gitlab_utils/
    test_pipeline_checker.py           → check_ci_pipeline()
    test_pipeline_checker_advanced.py  → edge cases for pipeline analysis
```

Run: `uv run pytest` or `uv run pytest -v`

## What NOT to add

- User profile views, leaderboards, or team scorecards
- MR quality evaluation (semantic commits, review coverage, time spent)
- Issue analytics
- Anything that queries user activity rather than project configuration
