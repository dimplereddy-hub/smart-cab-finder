import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from gitlab_compliance_checker.infrastructure.gitlab.pipeline_checker import check_ci_pipeline, check_precommit

from .docs_checker import check_docs, check_repo_files
from .file_classifier import classify_files
from .license_checker import check_license
from .metadata_checker import check_metadata
from .readme_checker import check_readme
from .speckit_checker import check_speckit
from .templates_checker import check_templates
from .tools_checker import check_tools


def run_project_compliance_checks(gl, project_id: int, ref: Optional[str] = None) -> Dict[str, Any]:
    """
    Ultimate entry point: Runs all production-grade compliance checks for a project.
    """
    try:
        project_info = gl._get(f"/projects/{project_id}")
        branch = ref or project_info.get("default_branch", "main")
    except Exception:
        branch = "main"

    # Run all independent checkers in parallel — cuts wall time from ~40s to ~5s
    checker_tasks = {
        "readme":     lambda: check_readme(gl, project_id, ref=branch),
        "license":    lambda: check_license(gl, project_id, ref=branch),
        "templates":  lambda: check_templates(gl, project_id, ref=branch),
        "metadata":   lambda: check_metadata(gl, project_id),
        "file_types": lambda: classify_files(gl, project_id, ref=branch),
        "tools":      lambda: check_tools(gl, project_id, ref=branch),
        "docs":       lambda: check_docs(gl, project_id, ref=branch),
        "repo_files": lambda: check_repo_files(gl, project_id, ref=branch),
        "speckit":    lambda: check_speckit(gl, project_id, ref=branch),
    }
    results: Dict[str, Any] = {"dx_ci": None, "precommit": None}
    with ThreadPoolExecutor(max_workers=len(checker_tasks)) as executor:
        futures = {executor.submit(fn): key for key, fn in checker_tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception:
                results[key] = {}

    # --- GitLab CI Deep Dive ---
    project_type = results["tools"].get("project_type", "Unknown")
    try:
        encoded_path = quote(".gitlab-ci.yml", safe="")
        f = gl._get(f"/projects/{project_id}/repository/files/{encoded_path}", params={"ref": branch})
        if f and isinstance(f, dict) and "content" in f:
            ci_content = base64.b64decode(f["content"]).decode("utf-8")
            results["dx_ci"] = check_ci_pipeline(ci_content, project_type=project_type)
    except Exception:
        pass

    # --- Pre-commit Hook Deep Dive ---
    try:
        from gitlab_compliance_checker.infrastructure.gitlab.parsers import parse_yaml

        encoded_path = quote(".pre-commit-config.yaml", safe="")
        f = gl._get(f"/projects/{project_id}/repository/files/{encoded_path}", params={"ref": branch})
        if f and isinstance(f, dict) and "content" in f:
            pc_content = base64.b64decode(f["content"]).decode("utf-8")
            results["precommit"] = check_precommit(parse_yaml(pc_content))
        else:
            results["precommit"] = check_precommit(None)
    except Exception:
        results["precommit"] = check_precommit(None)

    # Calculate overall compliance score from all checks
    _tools = results["tools"]
    _quality = _tools.get("quality_tools", {})
    _security = _tools.get("security", {})
    _testing = _tools.get("testing", {})
    _automation = _tools.get("automation", {})
    _speckit = results.get("speckit", {})
    _meta = results.get("metadata", {})
    _docs = results.get("docs", {})
    _license = results.get("license", {})

    all_checks = [
        # DX tools (8)
        _quality.get("ruff") or _quality.get("biome") or _quality.get("eslint"),
        _quality.get("mypy") or _quality.get("knip"),
        _security.get("secret_scanning"),
        _security.get("dependency_audit"),
        _testing.get("coverage"),
        _automation.get("git_cliff"),
        _automation.get("pre_commit"),
        _automation.get("gitlab_ci"),
        # Compliance (4)
        _license.get("valid", False),
        _docs.get("all_present", False),
        _meta.get("description_present", False),
        _meta.get("tags_present", False),
        # Spec-Kit (4)
        _speckit.get("setup_present", False),
        _speckit.get("constitution_present", False),
        _speckit.get("templates_present", False),
        _speckit.get("specs_dir_present", False),
    ]
    results["dx_score"] = int((sum(1 for c in all_checks if c) / len(all_checks)) * 100) if all_checks else 0

    return results


def get_dx_suggestions(report: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generates actionable suggestions based on the compliance report.
    """
    suggestions = []
    tools = report.get("tools", {})
    quality = tools.get("quality_tools", {})
    security = tools.get("security", {})
    automation = tools.get("automation", {})
    lang = tools.get("project_type", "Unknown")

    # --- Quality Tools ---
    if "Python" in lang:
        if not quality.get("ruff"):
            suggestions.append(
                {
                    "item": "Ruff",
                    "reason": "Missing industry-standard linter/formatter.",
                    "action": "`uv add --dev ruff` and add to `.pre-commit-config.yaml`",
                }
            )
        if not quality.get("mypy"):
            suggestions.append(
                {"item": "Mypy", "reason": "Type checking is essential for Python DX.", "action": "`uv add --dev mypy`"}
            )

    if "JavaScript" in lang or "TypeScript" in lang:
        if not quality.get("biome") and not quality.get("eslint"):
            suggestions.append(
                {
                    "item": "Biome/ESLint",
                    "reason": "Missing JS/TS linting.",
                    "action": "`npm install --save-dev @biomejs/biome` or `eslint`",
                }
            )
        if not quality.get("knip"):
            suggestions.append(
                {
                    "item": "Knip",
                    "reason": "Dead code checking improves maintainability.",
                    "action": "`npm install --save-dev knip`",
                }
            )

    # --- Security ---
    if not security.get("secret_scanning"):
        suggestions.append(
            {
                "item": "Secret Scanning",
                "reason": "Exposing secrets is a critical security risk.",
                "action": "Add `gitleaks` to pre-commit or enable GitLab Secret Detection.",
            }
        )

    # --- Automation ---
    if not automation.get("git_cliff"):
        suggestions.append(
            {
                "item": "Git-Cliff",
                "reason": "Automated changelogs from conventional commits.",
                "action": "Add `cliff.toml` and integrate with CI/CD.",
            }
        )

    # --- License & Docs ---
    if not report["license"].get("valid"):
        suggestions.append(
            {
                "item": "License",
                "reason": "Project must be licensed under AGPLv3.",
                "action": "Ensure the LICENSE file contains the full AGPLv3 text.",
            }
        )

    if report["readme"].get("needs_improvement"):
        suggestions.append(
            {
                "item": "README Quality",
                "reason": "Poor documentation hinders onboarding.",
                "action": "Add Installation, Usage, and Contributing sections.",
            }
        )

    docs = report.get("docs", {})
    for missing_doc in docs.get("missing", []):
        suggestions.append(
            {
                "item": f"Missing {missing_doc}",
                "reason": f"{missing_doc} is required for all team repositories.",
                "action": f"Create a detailed `{missing_doc}` file in the repository root.",
            }
        )

    repo_files = report.get("repo_files", {})
    for missing_file, info in repo_files.get("files", {}).items():
        if not info.get("present"):
            suggestions.append(
                {
                    "item": f"Missing {missing_file}",
                    "reason": info.get("reason", f"{missing_file} is missing."),
                    "action": f"Add `{missing_file}` to the repository root.",
                }
            )

    # --- CI Pipeline Suggestions ---
    dx_ci = report.get("dx_ci")
    if dx_ci and "recommendations" in dx_ci:
        for rec in dx_ci["recommendations"]:
            suggestions.append({"item": "CI Pipeline", "reason": rec["message"], "action": rec["command"]})

    # --- Spec-Kit (SDD) Suggestions ---
    speckit = report.get("speckit", {})
    if not speckit.get("setup_present"):
        suggestions.append(
            {
                "item": "Spec-Kit Setup",
                "reason": "No .specify/ directory found. Spec-Driven Development is not configured.",
                "action": "Run `npx @github/spec-kit init` or manually create `.specify/memory/constitution.md` and `.specify/templates/`.",
            }
        )
    elif not speckit.get("constitution_present"):
        suggestions.append(
            {
                "item": "Spec-Kit Constitution",
                "reason": "Missing `.specify/memory/constitution.md` — the project governing principles document.",
                "action": "Create `.specify/memory/constitution.md` defining project principles, tech stack, and development guidelines.",
            }
        )
    if speckit.get("setup_present") and not speckit.get("templates_present"):
        suggestions.append(
            {
                "item": "Spec-Kit Templates",
                "reason": "Missing one or more standard spec-kit templates (spec-template.md, plan-template.md, tasks-template.md).",
                "action": "Add the missing templates under `.specify/templates/` from the spec-kit repository.",
            }
        )
    if not speckit.get("specs_dir_present"):
        suggestions.append(
            {
                "item": "Spec-Kit Feature Specs",
                "reason": "No feature specs found under `specs/`. Use spec-driven development for new features.",
                "action": "Create `specs/<feature-name>/spec.md`, `plan.md`, and `tasks.md` for each feature.",
            }
        )

    return suggestions
