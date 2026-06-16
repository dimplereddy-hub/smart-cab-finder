from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from urllib.parse import quote

SPECKIT_CORE_FILES = [
    ".specify/memory/constitution.md",
    ".specify/templates/spec-template.md",
    ".specify/templates/plan-template.md",
    ".specify/templates/tasks-template.md",
]

FEATURE_SPEC_FILES = ["spec.md", "plan.md", "tasks.md"]


def _file_present(gl, project_id: int, filepath: str, ref: str) -> bool:
    try:
        encoded = quote(filepath, safe="")
        f = gl._get(f"/projects/{project_id}/repository/files/{encoded}", params={"ref": ref})
        return bool(f and isinstance(f, dict) and "content" in f)
    except Exception:
        return False


def _list_directory(gl, project_id: int, path: str, ref: str) -> List[str]:
    try:
        items = gl._get(
            f"/projects/{project_id}/repository/tree",
            params={"ref": ref, "path": path, "per_page": "100"},
        )
        if isinstance(items, list):
            return [item["name"] for item in items if isinstance(item, dict) and item.get("type") == "tree"]
        return []
    except Exception:
        return []


def check_speckit(gl, project_id: int, ref: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks for Spec-Kit (Spec-Driven Development) compliance.
    https://github.com/github/spec-kit
    """
    try:
        if not ref:
            project_info = gl._get(f"/projects/{project_id}")
            ref = project_info.get("default_branch", "main") if isinstance(project_info, dict) else "main"

        with ThreadPoolExecutor(max_workers=len(SPECKIT_CORE_FILES)) as executor:
            futures = {fp: executor.submit(_file_present, gl, project_id, fp, ref) for fp in SPECKIT_CORE_FILES}
            core_files_status: Dict[str, bool] = {fp: fut.result() for fp, fut in futures.items()}

        constitution_present = core_files_status[".specify/memory/constitution.md"]
        templates_present = all(
            core_files_status[f] for f in SPECKIT_CORE_FILES if "templates" in f
        )
        specify_dir_present = any(core_files_status.values())

        # Probe specs/ for feature spec directories
        spec_features: List[Dict[str, Any]] = []
        for feature_name in _list_directory(gl, project_id, "specs", ref):
            feature_files = {
                req: _file_present(gl, project_id, f"specs/{feature_name}/{req}", ref)
                for req in FEATURE_SPEC_FILES
            }
            spec_features.append(
                {
                    "name": feature_name,
                    "files": feature_files,
                    "complete": all(feature_files.values()),
                }
            )

        specs_dir_present = len(spec_features) > 0

        score_checks = [specify_dir_present, constitution_present, templates_present, specs_dir_present]
        score = int(sum(1 for c in score_checks if c) / len(score_checks) * 100)

        return {
            "setup_present": specify_dir_present,
            "constitution_present": constitution_present,
            "templates_present": templates_present,
            "core_files": core_files_status,
            "specs_dir_present": specs_dir_present,
            "spec_features": spec_features,
            "complete_specs_count": sum(1 for f in spec_features if f["complete"]),
            "score": score,
        }

    except Exception as e:
        return {"error": str(e), "setup_present": False, "constitution_present": False,
                "templates_present": False, "specs_dir_present": False, "spec_features": [],
                "complete_specs_count": 0, "score": 0}
