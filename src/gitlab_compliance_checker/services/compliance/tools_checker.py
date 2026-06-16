import base64
from typing import Any, Dict, Optional
from urllib.parse import quote

from gitlab_compliance_checker.infrastructure.gitlab.parsers import parse_json, parse_yaml


def check_tools(gl, project_id: int, ref: Optional[str] = None) -> Dict[str, Any]:
    """
    Ultimate DX-checker: Deep analysis of CLI tools and CI/CD pipelines.
    Checks for: ruff, uv audit, vulture, knip, mypy, git-cliff, secret scanning, etc.
    """
    try:
        if not ref:
            project_info = gl._get(f"/projects/{project_id}")
            ref = project_info.get("default_branch", "main")

        def get_file_content(filepath: str) -> str:
            try:
                encoded_path = quote(filepath, safe="")
                f = gl._get(f"/projects/{project_id}/repository/files/{encoded_path}", params={"ref": ref})
                if f and isinstance(f, dict) and "content" in f:
                    return base64.b64decode(f["content"]).decode("utf-8")
                return ""
            except Exception:
                return ""

        def file_exists(filepath: str) -> bool:
            try:
                encoded_path = quote(filepath, safe="")
                f = gl._get(f"/projects/{project_id}/repository/files/{encoded_path}", params={"ref": ref})
                return bool(f and isinstance(f, dict) and "content" in f)
            except Exception:
                return False

        # Detect project type by directly probing config files (avoids unreliable tree listing)
        project_subdir = ""
        if file_exists("pyproject.toml") or file_exists("requirements.txt") or file_exists("setup.py"):
            has_ts = file_exists("tsconfig.json")
            has_js = file_exists("package.json")
            if has_ts:
                project_type = "Python & TypeScript"
            elif has_js:
                project_type = "Python & JavaScript"
            else:
                project_type = "Python"
        elif file_exists("tsconfig.json"):
            project_type = "TypeScript"
        elif file_exists("package.json"):
            project_type = "JavaScript"
        else:
            # Probe one level into subdirectories using root tree
            project_type = "Unknown"
            try:
                root_items = gl._get(
                    f"/projects/{project_id}/repository/tree",
                    params={"ref": ref, "per_page": "100"},
                )
                subdirs = [item["name"] for item in (root_items or []) if item.get("type") == "tree"]
                for subdir in subdirs:
                    if file_exists(f"{subdir}/pyproject.toml") or file_exists(f"{subdir}/requirements.txt"):
                        project_subdir = subdir + "/"
                        has_ts = file_exists(f"{subdir}/tsconfig.json")
                        has_js = file_exists(f"{subdir}/package.json")
                        if has_ts:
                            project_type = "Python & TypeScript"
                        elif has_js:
                            project_type = "Python & JavaScript"
                        else:
                            project_type = "Python"
                        break
                    elif file_exists(f"{subdir}/tsconfig.json"):
                        project_subdir = subdir + "/"
                        project_type = "TypeScript"
                        break
                    elif file_exists(f"{subdir}/package.json"):
                        project_subdir = subdir + "/"
                        project_type = "JavaScript"
                        break
            except Exception:
                pass

        def get_file_content_with_subdir(filepath: str) -> str:
            """Try root first, then subdir (CI files live at root, tool configs may be in subdir)."""
            content = get_file_content(filepath)
            if not content and project_subdir:
                content = get_file_content(project_subdir + filepath)
            return content

        configs: Dict[str, Any] = {
            "gitlab_ci": parse_yaml(get_file_content_with_subdir(".gitlab-ci.yml")),
            "pre_commit": parse_yaml(get_file_content_with_subdir(".pre-commit-config.yaml")),
            "pyproject": get_file_content_with_subdir("pyproject.toml"),
            "package_json": parse_json(get_file_content_with_subdir("package.json")),
            "husky_pre_commit": get_file_content_with_subdir(".husky/pre-commit"),
            "cliff_toml": get_file_content_with_subdir("cliff.toml"),
        }

        # Initialize results
        quality_tools: Dict[str, Any] = {}
        security: Dict[str, Any] = {}
        testing: Dict[str, Any] = {}
        automation: Dict[str, Any] = {}
        i18n: Dict[str, Any] = {}

        pyproject_content = str(configs.get("pyproject", ""))
        pre_commit_content = str(configs.get("pre_commit", "")) + str(configs.get("husky_pre_commit", ""))
        gitlab_ci_content = str(configs.get("gitlab_ci", ""))

        # --- 1. Quality & Linting Tools ---
        ci_str = gitlab_ci_content.lower()
        pc_str = pre_commit_content.lower()
        py_str = pyproject_content.lower()

        if "Python" in project_type:
            quality_tools["ruff"] = "[tool.ruff]" in pyproject_content or "ruff" in pc_str or "ruff" in ci_str
            quality_tools["mypy"] = "[tool.mypy]" in pyproject_content or "mypy" in pc_str or "mypy" in ci_str
            quality_tools["vulture"] = (
                "[tool.vulture]" in pyproject_content or "vulture" in pc_str or "vulture" in ci_str
            )
            quality_tools["bandit"] = "[tool.bandit]" in pyproject_content or "bandit" in pc_str or "bandit" in ci_str
            quality_tools["pylint"] = "pylint" in pc_str or "pylint" in ci_str
            quality_tools["flake8"] = "flake8" in pc_str or "flake8" in ci_str
            quality_tools["semgrep"] = "semgrep" in pc_str or "semgrep" in ci_str
            quality_tools["pyupgrade"] = "pyupgrade" in pc_str or "pyupgrade" in ci_str

        if "JavaScript" in project_type or "TypeScript" in project_type:
            pkg = configs.get("package_json")
            if isinstance(pkg, dict):
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                quality_tools["eslint"] = "eslint" in deps or "eslint" in ci_str
                quality_tools["prettier"] = "prettier" in deps or "prettier" in ci_str
                quality_tools["biome"] = "biome" in deps or "biome" in ci_str
                quality_tools["oxlint"] = "oxlint" in deps or "oxlint" in ci_str
                quality_tools["knip"] = "knip" in deps or "knip" in ci_str
                quality_tools["husky"] = "husky" in deps or "husky" in ci_str

        # --- 2. Security & Secret Scanning ---
        security["secret_scanning"] = any(
            x in ci_str or x in pc_str
            for x in [
                "gitleaks",
                "trufflehog",
                "secret_detection",
                "detect-secrets",
                "git-secrets",
                "secretlint",
                "trivy secret",
                "checkov",
            ]
        )
        security["dependency_audit"] = any(
            x in ci_str or x in pc_str
            for x in [
                "uv audit",
                "uv-audit",
                "pip-audit",
                "npm audit",
                "yarn audit",
                "auditjs",
                "safety",
                "snyk",
                "dependabot",
                "owasp",
                "trivy",
                "grype",
                "osv-scanner",
            ]
        )
        security["sast"] = any(x in ci_str for x in ["sast", "semgrep", "sonarqube", "sonar-scanner", "codeql"])
        if "Python" in project_type:
            security["bandit"] = "bandit" in pc_str or "bandit" in ci_str or "[tool.bandit]" in pyproject_content

        # --- 3. Testing & Coverage ---
        if "Python" in project_type:
            testing["pytest"] = "pytest" in py_str or "pytest" in ci_str
            testing["hypothesis"] = "hypothesis" in py_str or "hypothesis" in ci_str
            testing["coverage"] = (
                "pytest-cov" in py_str or "--cov" in ci_str or "coverage" in ci_str or "codecov" in ci_str
            )
            testing["coverage_threshold"] = "fail-under" in py_str or "fail_under" in py_str

        if "JavaScript" in project_type or "TypeScript" in project_type:
            pkg = configs.get("package_json")
            if isinstance(pkg, dict):
                scripts = pkg.get("scripts", {})
                testing["jest_vitest"] = any(x in str(pkg) for x in ["jest", "vitest"])
                testing["coverage"] = any("coverage" in s for s in scripts.values())

        # --- 4. Automation & Changelog ---
        automation["git_cliff"] = configs["cliff_toml"] != "" or "git-cliff" in ci_str
        automation["pre_commit"] = configs["pre_commit"] is not None or quality_tools.get("husky")
        automation["gitlab_ci"] = configs["gitlab_ci"] is not None

        # --- 5. Internationalization (i18n) ---
        i18n["supported"] = any(
            x in (ci_str + pc_str + str(configs["pyproject"]) + str(configs["package_json"]))
            for x in ["babel", "gettext", "i18next", "react-intl"]
        )

        return {
            "project_type": project_type,
            "quality_tools": quality_tools,
            "security": security,
            "testing": testing,
            "automation": automation,
            "i18n": i18n,
        }

    except Exception as e:
        return {"error": str(e)}
