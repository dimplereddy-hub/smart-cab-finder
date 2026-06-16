from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional
from urllib.parse import quote

REQUIRED_DOCS = ["README.md", "CONTRIBUTING.md", "USER_MANUAL.md", "AGENTS.md"]

REQUIRED_REPO_FILES = [
    (".gitignore", "Prevents secrets/build artifacts from being committed"),
    (".editorconfig", "Enforces consistent code style across editors"),
    ("CHANGELOG.md", "Documents release history"),
    ("SECURITY.md", "Responsible disclosure policy"),
    ("CODE_OF_CONDUCT.md", "Community standards"),
    (".env.example", "Shows required env vars without exposing values"),
    ("Dockerfile", "Containerization readiness"),
    (".dockerignore", "Keeps Docker images lean and safe"),
]


def _file_present(gl, project_id: int, filename: str, ref: str) -> bool:
    try:
        encoded = quote(filename, safe="")
        f = gl._get(f"/projects/{project_id}/repository/files/{encoded}", params={"ref": ref})
        return bool(f and isinstance(f, dict) and "content" in f)
    except Exception:
        return False


def _resolve_ref(gl, project_id: int, ref: Optional[str]) -> str:
    if ref:
        return ref
    try:
        info = gl._get(f"/projects/{project_id}")
        if isinstance(info, dict):
            return str(info.get("default_branch", "main"))
        return "main"
    except Exception:
        return "main"


def check_docs(gl, project_id: int, ref: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks for the presence of required documentation files in the repository root.
    Required: README.md, CONTRIBUTING.md, USER_MANUAL.md, AGENTS.md
    """
    ref = _resolve_ref(gl, project_id, ref)

    with ThreadPoolExecutor(max_workers=len(REQUIRED_DOCS)) as executor:
        futures = {doc: executor.submit(_file_present, gl, project_id, doc, ref) for doc in REQUIRED_DOCS}
        files_status: Dict[str, bool] = {doc: fut.result() for doc, fut in futures.items()}

    all_present = all(files_status.values())
    missing = [doc for doc, present in files_status.items() if not present]

    return {
        "files": files_status,
        "all_present": all_present,
        "missing": missing,
    }


def check_repo_files(gl, project_id: int, ref: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks presence of standard repository health files every team project should have.
    """
    ref = _resolve_ref(gl, project_id, ref)

    with ThreadPoolExecutor(max_workers=len(REQUIRED_REPO_FILES)) as executor:
        futures = {filename: executor.submit(_file_present, gl, project_id, filename, ref)
                   for filename, _ in REQUIRED_REPO_FILES}
        files_status: Dict[str, Dict[str, Any]] = {
            filename: {"present": futures[filename].result(), "reason": reason}
            for filename, reason in REQUIRED_REPO_FILES
        }

    missing = [name for name, info in files_status.items() if not info["present"]]

    return {
        "files": files_status,
        "all_present": len(missing) == 0,
        "missing": missing,
        "score": round((len(files_status) - len(missing)) / len(files_status) * 100),
    }
