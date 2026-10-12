from pathlib import Path

from langchain_core.tools import tool

from agent.app.config import Settings
from agent.sandbox.paths import PathViolationError, resolve_for_root


def make_fs_tools(settings: Settings) -> list:
    ingest_root = settings.ingest_path
    workspace_root = settings.workspace_path
    max_write = settings.max_write_bytes
    max_read = settings.max_read_bytes

    @tool
    def list_files(root: str = "ingest", subpath: str = "") -> str:
        """List files under ingest (read-only uploads) or workspace (agent output)."""
        try:
            base = resolve_for_root(root, subpath or ".", ingest_root, workspace_root)
            if not base.is_dir():
                return f"{root}/{subpath} is not a directory."
            entries = []
            for item in sorted(base.iterdir())[:200]:
                kind = "dir" if item.is_dir() else "file"
                entries.append(f"{kind}\t{item.name}")
            return "\n".join(entries) or "(empty)"
        except PathViolationError as exc:
            return str(exc)

    @tool
    def read_file(relative_path: str, root: str = "ingest", max_chars: int = 8000) -> str:
        """Read a text file from ingest or workspace (bounded size)."""
        try:
            path = resolve_for_root(
                root,
                relative_path,
                ingest_root,
                workspace_root,
                must_exist=True,
            )
            if not path.is_file():
                return "Not a file."
            size = path.stat().st_size
            if size > max_read:
                return f"File too large ({size} bytes). Max read is {max_read}."
            limit = min(max(max_chars, 1), max_read)
            text = path.read_text(encoding="utf-8", errors="replace")
            return text[:limit]
        except PathViolationError as exc:
            return str(exc)

    @tool
    def write_file(relative_path: str, content: str) -> str:
        """Write a text file under workspace only (for data prep, not HTML artifacts)."""
        try:
            path = resolve_for_root(
                "workspace",
                relative_path,
                ingest_root,
                workspace_root,
            )
            encoded = content.encode("utf-8")
            if len(encoded) > max_write:
                return f"Content too large ({len(encoded)} bytes). Max write is {max_write}."
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Wrote workspace/{relative_path} ({len(encoded)} bytes)."
        except PathViolationError as exc:
            return str(exc)

    return [list_files, read_file, write_file]
