# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.0.0] - 2026-05-30

### Changed — Focus: Compliance-only

- Removed all non-compliance features: User Profile Overview, Team Leaderboard, and Batch Analytics (MR/issue scorecarding)
- App now launches directly into Project Compliance Analysis — no mode selector
- Batch tab now analyses project repository compliance (not user MR/issue activity)

### Added

- **Documentation Files check**: verifies README.md, CONTRIBUTING.md, USER_MANUAL.md, AGENTS.md are present
- **Repository Health Files check**: verifies .gitignore, .editorconfig, CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md, .env.example, Dockerfile, .dockerignore
- **Pre-commit Hook Analysis**: stage-by-stage breakdown (lint, format, type_check, security, quality) with detected hook names
- **Score Breakdown expander**: shows which of the 8 checks passed/failed and why, visible in both single and batch views
- **Branch selection in batch analysis**: single branch name applied to all projects with automatic fallback to each project's default branch
- **Subdirectory detection**: language detection now probes one level into subdirectories when config files are not found at repo root
- **Expanded tool detection**: added 50+ additional tools across lint, format, type_check, coverage, and security categories
- **Stage name normalisation**: CI stage names with hyphens (e.g. `type-check`) now correctly match underscore-named expected stages (`type_check`)
- **Single-page compliance report**: replaced tabbed layout with a scrollable single-page report
- **Batch project cards**: each project in batch view renders as a bordered card with score colour indicator (🟢🟡🔴), metrics row, and expandable full report

### Fixed

- Fixed project type always returning "Unknown" when `_get_paginated` failed silently due to conflicting `path` keyword argument
- Fixed coverage not detected when pytest uses `--cov` flag (no separate `coverage` stage)
- Fixed `--cov` flag not matching due to word-boundary regex; now uses substring match for flag-style tools
- Fixed `ruff` not detected as a format tool (only was in lint tools)
- Removed ~300 lines of dead MR/issue evaluation code from `client.py`

## [1.0.0] - 2025-07-28

### Added

- Core compliance checking: README, LICENSE (AGPLv3), issue/MR templates, metadata, tools, CI pipeline
- Streamlit UI with single project and batch project modes
- Docker support and deployment scripts
- GitLab async client with rate-limit handling and retry logic

## [0.1.0] - 2025-06-15

- Prototype with basic project and user compliance checks
