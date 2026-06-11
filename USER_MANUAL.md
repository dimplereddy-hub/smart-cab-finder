# User Manual — GitLab Compliance Checker

## Overview

GitLab Compliance Checker is a Streamlit web app that analyses GitLab project repositories and produces a detailed compliance report. It checks whether a project meets documentation, tooling, security, and CI/CD standards, and gives a scored breakdown with actionable suggestions.

## Getting Started

### Prerequisites

- A GitLab account with access to the repositories you want to analyse
- A GitLab Personal Access Token with at minimum `read_api` scope

### Creating a Personal Access Token

1. Log in to your GitLab instance
2. Go to **User Settings → Access Tokens**
3. Enter a name (e.g. `compliance-checker`)
4. Set an expiry date
5. Select scope: `read_api`
6. Click **Create personal access token**
7. Copy the token immediately — it is shown only once

### Starting the App

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Sidebar Configuration

| Field | Description |
|---|---|
| **GitLab URL** | Base URL of your GitLab instance (e.g. `https://code.swecha.org`) |
| **GitLab Token** | Your personal access token |
| **Verify SSL** | Uncheck only for self-hosted instances with self-signed certificates |

---

## Single Project Analysis

### Step 1 — Enter the project

Paste a project URL or ID into the input field:

```
https://code.swecha.org/group/project.git
```

Click **Fetch Project & Branches**.

### Step 2 — Select a branch

Choose the branch to analyse from the dropdown (defaults to the project's default branch).

### Step 3 — Run the analysis

Click **Run Compliance Analysis**. The report appears below.

---

## Reading the Report

### Summary Metrics (top row)

| Metric | Meaning |
|---|---|
| **Compliance Score** | Percentage of the 8 core checks that passed |
| **Stack** | Detected language (Python, JavaScript, TypeScript, or Unknown) |
| **AGPLv3 Compliance** | Whether a valid AGPLv3 LICENSE file was found |
| **Documentation** | Whether all 4 required doc files are present |

### Score Breakdown

Click **📊 Score Breakdown** to see exactly which checks passed or failed and why.

The 8 checks, each worth 12.5%:

| Check | What is looked for |
|---|---|
| Linter | ruff / biome / eslint in pyproject.toml or pre-commit config |
| Type Checker | mypy / knip |
| Secret Scanning | gitleaks / trufflehog / detect-secrets in CI or pre-commit |
| Dependency Audit | pip-audit / npm audit / snyk / uv audit |
| Coverage Reporting | pytest-cov / --cov flag / codecov |
| Changelog Automation | cliff.toml present or git-cliff in CI |
| Pre-commit Hooks | .pre-commit-config.yaml present |
| GitLab CI Pipeline | .gitlab-ci.yml present |

### Report Sections

| Section | What it shows |
|---|---|
| **📝 Metadata** | GitLab project description and Git tags |
| **📄 Documentation Files** | README.md, CONTRIBUTING.md, USER_MANUAL.md, AGENTS.md — ✅/❌ per file |
| **🗂 Repository Health Files** | .gitignore, .editorconfig, CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md, .env.example, Dockerfile, .dockerignore |
| **🛠 Quality & Tools** | Linting and type-checking tools detected in config files |
| **🔒 Security** | Secret scanning, dependency audit, SAST tools |
| **🧪 Testing** | Test framework, coverage reporting, enforced thresholds |
| **🤖 Automation & CI** | GitLab CI, pre-commit, git-cliff; CI Pipeline Analysis; Pre-commit Hook Analysis |
| **📌 Suggestions** | Actionable fix instructions for every failed check |

### CI Pipeline Analysis

Shows each expected stage (test, lint, format, type_check, coverage) with:
- **Job** ✅/❌ — whether an active job exists for the stage
- **Tool** ✅/❌ — whether a known tool was detected in the job script
- **Tools** — list of detected tool names

Pipeline quality issues are shown with severity icons:
- 🔴 Error — stage or job is missing
- 🟡 Warning — stage present but no recognised tool detected

### Pre-commit Hook Analysis

Shows 5 categories (Lint, Format, Type Check, Security, Quality) with:
- ✅/❌ per category
- Names of detected hooks beneath each category

---

## Batch Project Analysis

### Setup

1. Click the **Batch Projects** tab
2. Enter one project URL or ID per line in the text area
3. Enter a branch name (default: `main`) — applied to all projects; falls back to each project's default branch if not found
4. Click **Run Batch Analysis**

### Reading batch results

Each project appears as a bordered card showing:
- Score colour: 🟢 ≥75% · 🟡 ≥40% · 🔴 <40%
- Project name, branch analysed, score %, and detected stack
- Five metric badges: AGPLv3, Security, Coverage, CI/CD, Pre-commit

Click **📋 View Full Compliance Report** on any card to expand the complete report — identical to the single project view.

---

## Interpreting Results

### What "Unknown" stack means

The language detector looks for `pyproject.toml`, `requirements.txt`, `package.json`, or `tsconfig.json` at the repository root and one level deep. If none are found, the stack shows "Unknown" and quality tool checks are skipped.

**Fix:** Ensure language config files are in the repo root or one subdirectory level.

### What affects the score

Only the 8 core checks listed in the Score Breakdown affect the percentage score. Documentation files, repository health files, and metadata are shown separately and appear in the Suggestions section but do not change the score number.

### Suggestions

Every failed check generates a suggestion card in the **📌 Suggestions** section with:
- What is missing
- Why it matters
- The exact command or action to fix it

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| "Please enter a GitLab Token" warning | Token field is empty | Enter your PAT in the sidebar |
| "Critical Error initializing GitLab client" | Wrong URL or token | Check GitLab URL and token validity |
| Project not found | Wrong URL format or insufficient token scope | Ensure URL is correct and token has `read_api` |
| Stack shows "Unknown" | No language config at root or one level deep | See "What Unknown stack means" above |
| Score lower than expected | Check Score Breakdown for which checks failed | Follow the Suggestions section |
| SSL error | Self-signed certificate on self-hosted instance | Uncheck "Verify SSL" in sidebar |
