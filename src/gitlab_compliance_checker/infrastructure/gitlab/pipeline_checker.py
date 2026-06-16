import re
from typing import Any, Dict, List

import yaml

EXPECTED_STAGES = ["test", "lint", "format", "type_check", "coverage"]

STAGE_TOOLS = {
    "test": [
        # Python
        "pytest",
        "unittest",
        "nose",
        "nose2",
        "doctest",
        "hypothesis",
        "behave",
        "robot",
        # JavaScript / TypeScript
        "jest",
        "vitest",
        "mocha",
        "ava",
        "jasmine",
        "karma",
        "qunit",
        "tape",
        # E2E
        "cypress",
        "playwright",
        "selenium",
        "puppeteer",
        "testcafe",
        # Package-manager runners
        "npm test",
        "npm run test",
        "bun test",
        "yarn test",
        "pnpm test",
        # Other
        "go test",
        "cargo test",
        "mvn test",
        "gradle test",
    ],
    "lint": [
        # Python
        "ruff",
        "flake8",
        "pylint",
        "pyflakes",
        "pycodestyle",
        "pydocstyle",
        "prospector",
        "vulture",
        "bandit",
        "semgrep",
        "pylama",
        "wemake",
        "pyupgrade",
        "autoflake",
        "isort",
        # JavaScript / TypeScript
        "eslint",
        "biome",
        "jshint",
        "tslint",
        "oxlint",
        # Styles
        "stylelint",
        # Shell / Infra
        "shellcheck",
        "hadolint",
        "yamllint",
        "jsonlint",
        "markdownlint",
        "tflint",
        "golangci-lint",
        "staticcheck",
        # Generic
        "sonar",
        "sonarqube",
        "codeclimate",
        "megalinter",
        "super-linter",
    ],
    "format": [
        # Python
        "ruff",
        "black",
        "blue",
        "autopep8",
        "yapf",
        "isort",
        "pyupgrade",
        # JavaScript / TypeScript
        "prettier",
        "biome",
        # Other languages
        "clang-format",
        "gofmt",
        "rustfmt",
        "shfmt",
        "ktlint",
        "spotless",
        "google-java-format",
    ],
    "type_check": [
        # Python
        "mypy",
        "pyright",
        "pytype",
        "pyre",
        "beartype",
        "typeguard",
        "ty",
        # JavaScript / TypeScript
        "tsc",
        "typescript",
        "flow",
        # Other
        "sorbet",
    ],
    "coverage": [
        # Flag-style (substring match)
        "--cov",
        "--coverage",
        "--cov-report",
        # Python
        "coverage",
        "pytest-cov",
        "pytest --cov",
        "coveralls",
        "codecov",
        # JavaScript
        "istanbul",
        "nyc",
        "c8",
        "vitest run --coverage",
        # Other
        "lcov",
        "gcov",
        "jacoco",
        "cobertura",
        "simplecov",
    ],
}

# New weighted scoring per stage
STAGE_WEIGHTS = {
    "test": 3,
    "lint": 2,
    "format": 1,
    "type_check": 2,
    "coverage": 2,
}


def _parse_yaml(content: str) -> Dict[str, Any]:
    """
    Robust YAML parsing using yaml.safe_load.
    Handles empty, invalid, or non-dictionary YAML safely.
    """
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return data
        return {}
    except yaml.YAMLError:
        return {}


def contains_tool(script_text: str, tools: List[str]) -> List[str]:
    """
    Returns list of detected tools using regex or substring matching.
    Flag-style tools (e.g. --cov) use plain substring matching since they
    have no word boundary before the leading dashes.
    """
    detected = []
    for tool in tools:
        if tool.startswith("-"):
            # e.g. "--cov" — match as a plain substring
            if tool.lower() in script_text.lower():
                detected.append(tool)
        else:
            pattern = rf"\b{re.escape(tool)}\b"
            if re.search(pattern, script_text, re.IGNORECASE):
                detected.append(tool)
    return detected


def is_active_job(job: Dict[str, Any]) -> bool:
    """
    Filters out inactive jobs (e.g., when: manual).
    Explicitly ignores jobs with unconditional rules: when: never.
    """
    # 1. Ignore manual jobs
    if job.get("when") == "manual":
        return False

    # 2. Advanced rules handling: ignore jobs with unconditional'when: never'
    rules = job.get("rules")
    if isinstance(rules, list):
        for rule in rules:
            if isinstance(rule, dict):
                # An unconditional "when: never" rule means the job is inactive.
                # If there's an "if" condition, it's considered active for our heuristic.
                if rule.get("when") == "never" and "if" not in rule:
                    return False

    return True


def check_ci_pipeline(ci_content: str, project_type: str = "Unknown") -> Dict[str, Any]:
    """
    Refined DX CI Pipeline Analyzer.
    Validates stages, jobs, tool usage, and provides insights with severity classification.
    """
    parsed_yaml = _parse_yaml(ci_content)
    if not ci_content.strip():
        return {
            "error": "Empty .gitlab-ci.yml content",
            "stages_present": [],
            "missing_stages": EXPECTED_STAGES,
            "jobs": {},
            "issues": [
                {
                    "message": "Empty .gitlab-ci.yml content",
                    "severity": "error",
                }
            ],
            "dx_score": 0,
        }

    issues: List[Dict[str, str]] = []
    if not parsed_yaml:
        issues.append({"message": "Invalid or non-dictionary YAML content", "severity": "error"})
        parsed_yaml = {}

    # 1. Explicit vs Implicit Stages Detection
    has_explicit_stages = "stages" in parsed_yaml and isinstance(parsed_yaml["stages"], list)
    if not has_explicit_stages:
        issues.append({"message": "No explicit 'stages:' defined in CI", "severity": "warning"})

    # 1b. Check for includes (which might define stages/jobs elsewhere)
    has_includes = "include" in parsed_yaml
    if has_includes:
        issues.append(
            {
                "message": "CI uses 'include:', which may define stages or jobs not visible to this analyzer.",
                "severity": "info",
            }
        )

    # 2. Extract defined stages (normalize hyphens → underscores to match EXPECTED_STAGES)
    defined_stages = set()
    if has_explicit_stages:
        defined_stages.update([str(s).replace("-", "_") for s in parsed_yaml["stages"]])

    # 3. Extract and filter active jobs
    active_jobs = {}
    for key, value in parsed_yaml.items():
        # Valid jobs must be dicts, contain a 'script' key, and NOT start with '.'
        if isinstance(value, dict) and "script" in value:
            # Skip hidden jobs (GitLab hidden jobs start with .)
            if key.startswith("."):
                continue

            if is_active_job(value):
                # Normalize script to list of strings
                script = value["script"]
                if isinstance(script, str):
                    script = [script]
                elif not isinstance(script, list):
                    script = [str(script)]

                job_stage = str(value.get("stage", "test")).replace("-", "_")
                active_jobs[key] = {"stage": job_stage, "script": script}
                defined_stages.add(job_stage)

    # 4. Results initialization
    stages_present_all = [s for s in EXPECTED_STAGES if s in defined_stages]
    missing_stages = [s for s in EXPECTED_STAGES if s not in defined_stages]

    result: Dict[str, Any] = {
        "stages_present": stages_present_all,
        "missing_stages": missing_stages,
        "jobs": {},
        "issues": issues,
    }

    # 5. Core Stage Validation
    for req_stage in EXPECTED_STAGES:
        stage_present = req_stage in defined_stages

        # Find all jobs for this stage
        jobs_for_stage = [name for name, details in active_jobs.items() if details["stage"] == req_stage]
        job_present = len(jobs_for_stage) > 0

        detected_tools: List[str] = []
        indirect_execution = False
        if job_present:
            # Aggregate all script text for this stage
            all_script_text = "\n".join(["\n".join(active_jobs[j]["script"]) for j in jobs_for_stage])
            detected_tools = contains_tool(all_script_text, STAGE_TOOLS[req_stage])

            # Detect indirect script execution
            indirect_match = re.search(r"\b(bash|sh|make)\b", all_script_text, re.IGNORECASE)
            if indirect_match:
                indirect_execution = True

        result["jobs"][req_stage] = {
            "stage_present": stage_present,
            "job_present": job_present,
            "tool_detected": len(detected_tools) > 0,
            "job_names": jobs_for_stage,
            "detected_tools": detected_tools,
            "indirect_execution": indirect_execution,
        }

        # Issue generation logic
        if not stage_present:
            result["issues"].append({"message": f"Missing stage: {req_stage}", "severity": "error"})
        elif not job_present:
            result["issues"].append({"message": f"No active job defined for stage '{req_stage}'", "severity": "error"})
        elif not detected_tools:
            tools_str = "/".join(STAGE_TOOLS[req_stage])
            result["issues"].append(
                {
                    "message": f"Stage '{req_stage}' missing expected tools ({tools_str})",
                    "severity": "warning",
                }
            )

        if indirect_execution:
            result["issues"].append(
                {
                    "message": f"Tool detection for '{req_stage}' may be incomplete due to indirect script execution (bash/sh/make)",
                    "severity": "warning",
                }
            )

    # 6. Coverage Fallback Logic
    cov_result = result["jobs"]["coverage"]
    if not cov_result["stage_present"] or not cov_result["job_present"]:
        # Check 'test' stage for coverage tools
        test_jobs_names = result["jobs"]["test"]["job_names"]
        if test_jobs_names:
            test_script_text = "\n".join(["\n".join(active_jobs[j]["script"]) for j in test_jobs_names])
            # Detect coverage tools specifically
            test_detected_cov = contains_tool(test_script_text, STAGE_TOOLS["coverage"])
            if test_detected_cov:
                result["jobs"]["coverage"].update(
                    {
                        "tool_detected": True,
                        "note": "Coverage detected in test stage",
                        "detected_tools": test_detected_cov,
                    }
                )
                # Remove the error issue for missing coverage stage if tool is found in test
                result["issues"] = [
                    i
                    for i in result["issues"]
                    if not (
                        i["message"] == "Missing stage: coverage"
                        or i["message"] == "No active job defined for stage 'coverage'"
                    )
                ]

    # 7. Weighted DX Score Calculation (Bonus)
    # Weighted by importance per stage
    total_possible_score = sum(STAGE_WEIGHTS.values())
    raw_score = 0.0
    for req_stage, weight in STAGE_WEIGHTS.items():
        details = result["jobs"][req_stage]
        if details["stage_present"] and details["job_present"]:
            raw_score += weight * 0.5  # 50% for having the stage/job
            if details["tool_detected"]:
                raw_score += weight * 0.5  # 50% for detecting the actual tool

    # Normalize to 10
    result["dx_score"] = round((raw_score / total_possible_score) * 10, 1)

    # 8. Structured Recommendations (Bonus)
    recommendations = []
    is_python = "Python" in project_type
    is_js_ts = any(x in project_type for x in ["JavaScript", "TypeScript", "JS/TS"])

    if not result["jobs"]["lint"]["tool_detected"]:
        if is_python:
            recommendations.append(
                {"message": "Add Ruff for linting", "command": "uv add --dev ruff && ruff check .", "severity": "high"}
            )
        elif is_js_ts:
            recommendations.append(
                {
                    "message": "Add ESLint or Biome for linting",
                    "command": "npm install --save-dev eslint OR npm install --save-dev @biomejs/biome",
                    "severity": "high",
                }
            )

    if not result["jobs"]["format"]["tool_detected"]:
        if is_python:
            recommendations.append(
                {"message": "Add Ruff for formatting", "command": "ruff format .", "severity": "medium"}
            )
        elif is_js_ts:
            recommendations.append(
                {
                    "message": "Add Prettier for formatting",
                    "command": "npm install --save-dev prettier",
                    "severity": "medium",
                }
            )

    if not result["jobs"]["coverage"]["tool_detected"]:
        if is_python:
            recommendations.append(
                {
                    "message": "Add coverage reporting",
                    "command": "uv add --dev pytest-cov && pytest --cov=.",
                    "severity": "high",
                }
            )
        elif is_js_ts:
            recommendations.append(
                {
                    "message": "Add coverage reporting (Jest/Vitest)",
                    "command": "npm test -- --coverage",
                    "severity": "high",
                }
            )

    if not result["jobs"]["type_check"]["tool_detected"]:
        if is_python:
            recommendations.append(
                {
                    "message": "Add Mypy for type checking",
                    "command": "uv add --dev mypy && mypy .",
                    "severity": "medium",
                }
            )
        elif is_js_ts:
            recommendations.append(
                {
                    "message": "Add TypeScript for type checking",
                    "command": "npm install --save-dev typescript && npx tsc",
                    "severity": "medium",
                }
            )

    result["recommendations"] = recommendations

    return result


# ---------------------------------------------------------------------------
# Pre-commit Hook Analyzer
# ---------------------------------------------------------------------------

PRECOMMIT_CATEGORIES = {
    "lint": {
        "label": "Lint",
        "hooks": [
            "ruff",
            "flake8",
            "pylint",
            "eslint",
            "biome",
            "oxlint",
            "shellcheck",
            "hadolint",
            "yamllint",
            "markdownlint",
            "pylama",
            "pycodestyle",
            "pydocstyle",
            "autoflake",
        ],
    },
    "format": {
        "label": "Format",
        "hooks": [
            "ruff-format",
            "black",
            "isort",
            "prettier",
            "autopep8",
            "yapf",
            "blue",
            "pyupgrade",
            "shfmt",
        ],
    },
    "type_check": {
        "label": "Type Check",
        "hooks": ["mypy", "pyright", "pytype", "pyre"],
    },
    "security": {
        "label": "Security",
        "hooks": [
            "gitleaks",
            "detect-secrets",
            "bandit",
            "semgrep",
            "trufflehog",
            "checkov",
            "secretlint",
            "pip-audit",
            "safety",
        ],
    },
    "quality": {
        "label": "Quality",
        "hooks": [
            "vulture",
            "commitizen",
            "commitlint",
            "pyupgrade",
            "trailing-whitespace",
            "end-of-file-fixer",
            "check-yaml",
            "check-json",
            "check-toml",
            "check-merge-conflict",
            "debug-statements",
            "mixed-line-ending",
            "no-commit-to-branch",
        ],
    },
}


def check_precommit(pre_commit_yaml: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes a parsed .pre-commit-config.yaml and categorizes detected hooks.
    Returns a structure parallel to check_ci_pipeline() for uniform UI rendering.
    """
    if not pre_commit_yaml or not isinstance(pre_commit_yaml, dict):
        return {
            "available": False,
            "categories": {},
            "all_hooks": [],
            "repo_count": 0,
            "issues": [{"message": ".pre-commit-config.yaml not found or empty", "severity": "error"}],
        }

    repos = pre_commit_yaml.get("repos", [])
    all_hook_ids: List[str] = []

    for repo in repos:
        for hook in repo.get("hooks", []):
            hook_id = hook.get("id", "").lower()
            if hook_id:
                all_hook_ids.append(hook_id)

    categories: Dict[str, Any] = {}
    for cat_key, cat_info in PRECOMMIT_CATEGORIES.items():
        detected = [h for h in cat_info["hooks"] if h in all_hook_ids]
        categories[cat_key] = {
            "label": cat_info["label"],
            "detected": detected,
            "present": len(detected) > 0,
        }

    issues: List[Dict[str, str]] = []
    if not categories["security"]["present"]:
        issues.append({"message": "No security hooks configured (gitleaks/bandit/detect-secrets)", "severity": "error"})
    if not categories["lint"]["present"]:
        issues.append({"message": "No linting hooks configured", "severity": "warning"})
    if not categories["format"]["present"]:
        issues.append({"message": "No formatting hooks configured", "severity": "warning"})
    if not categories["type_check"]["present"]:
        issues.append({"message": "No type-checking hooks configured", "severity": "warning"})

    return {
        "available": True,
        "categories": categories,
        "all_hooks": all_hook_ids,
        "repo_count": len(repos),
        "issues": issues,
    }
