from enum import Enum
from pathlib import Path


class SandboxRoot(str, Enum):
    INGEST = "ingest"
    WORKSPACE = "workspace"


class PathViolationError(ValueError):
    pass


def resolve_under(root: Path, relative_path: str, *, must_exist: bool = False) -> Path:
    root = root.resolve()
    rel = relative_path.strip().lstrip("/").replace("\\", "/")
    if not rel or rel in (".", "..") or ".." in rel.split("/"):
        raise PathViolationError("Path must be a relative path without '..' segments.")

    candidate = (root / rel).resolve()
    if not str(candidate).startswith(str(root)):
        raise PathViolationError("Path escapes sandbox root.")

    if must_exist and not candidate.exists():
        raise PathViolationError(f"Not found: {relative_path}")

    return candidate


def resolve_for_root(
    root_kind: str,
    relative_path: str,
    ingest_root: Path,
    workspace_root: Path,
    *,
    must_exist: bool = False,
) -> Path:
    kind = root_kind.strip().lower()
    if kind == SandboxRoot.INGEST.value:
        return resolve_under(ingest_root, relative_path, must_exist=must_exist)
    if kind == SandboxRoot.WORKSPACE.value:
        return resolve_under(workspace_root, relative_path, must_exist=must_exist)
    raise PathViolationError("root must be 'ingest' or 'workspace'.")
