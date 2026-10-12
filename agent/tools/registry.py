from pathlib import Path

from langchain_core.tools import tool
from langchain_postgres import PGVector
from langgraph.types import interrupt

from agent.app.config import Settings
from agent.rag.ingest import ingest_directory
from agent.sandbox.paths import PathViolationError, resolve_for_root
from agent.tools.fs_tools import make_fs_tools
from agent.tools.script_tools import make_script_tools


def build_tools(
    settings: Settings,
    profile: dict,
    vectorstore: PGVector,
) -> list:
    ingest_root = settings.ingest_path
    workspace_root = settings.workspace_path
    rag_cfg = profile.get("rag") or {}
    hitl_cfg = profile.get("hitl") or {}
    hitl_enabled = bool(hitl_cfg.get("enabled", False))
    default_artifact = (profile.get("artifacts") or {}).get("default_filename", "summary.html")

    @tool
    def ingest_scan() -> str:
        """Scan the LAN upload folder (/ingest), embed new or changed text files into Postgres RAG."""
        result = ingest_directory(
            ingest_root,
            vectorstore,
            manifest_dir=workspace_root,
            chunk_size=int(rag_cfg.get("chunk_size", 1000)),
            chunk_overlap=int(rag_cfg.get("chunk_overlap", 150)),
        )
        return (
            f"Ingest complete: {result['ingested_files']} files, "
            f"{result['chunks']} chunks, {result['skipped']} skipped."
            + (f" Errors: {result['errors']}" if result["errors"] else "")
        )

    @tool
    def rag_search(query: str, k: int = 4) -> str:
        """Search embedded documents for context relevant to the user question."""
        docs = vectorstore.similarity_search(query, k=min(max(k, 1), 8))
        if not docs:
            return "No matching chunks in the vector store. Run ingest_scan after adding files to /ingest."
        parts = []
        for i, doc in enumerate(docs, start=1):
            src = doc.metadata.get("source", "?")
            snippet = doc.page_content[:800].replace("\n", " ")
            parts.append(f"[{i}] source={src}\n{snippet}")
        return "\n\n".join(parts)

    @tool
    def extract_structured(relative_path: str, max_chars: int = 2500) -> str:
        """Read a file under /ingest by relative path and return a text excerpt for analysis."""
        try:
            safe_path = resolve_for_root(
                "ingest",
                relative_path,
                ingest_root,
                workspace_root,
                must_exist=True,
            )
        except PathViolationError as exc:
            return str(exc)

        text = safe_path.read_text(encoding="utf-8", errors="replace")
        excerpt = text[: min(max_chars, 8000)]
        return f"File: {relative_path}\nLength: {len(text)} chars\n---\n{excerpt}"

    def _write_html_to_workspace(name: str, html_content: str) -> str:
        out = (workspace_root / name).resolve()
        root = workspace_root.resolve()
        if not str(out).startswith(str(root)):
            return "Invalid artifact filename."
        out.write_text(html_content, encoding="utf-8")
        return f"ARTIFACT:{name}"

    @tool
    def write_html_artifact(html_content: str, filename: str = "") -> str:
        """Write an interactive HTML summary (charts/diagrams) to /workspace for UI preview."""
        name = (filename or default_artifact).strip() or default_artifact
        name = Path(name).name
        if not name.endswith(".html"):
            name = f"{name}.html"

        preview = html_content[:1200]
        if hitl_enabled:
            decision = interrupt(
                {
                    "type": "html_artifact",
                    "filename": name,
                    "preview_html": preview,
                    "message": "Approve publishing this HTML artifact to the LAN UI?",
                }
            )
            if decision is False or (isinstance(decision, dict) and not decision.get("approved", True)):
                return "Artifact publish rejected by human review."

        return _write_html_to_workspace(name, html_content)

    @tool
    def register_artifact(filename: str) -> str:
        """Register an existing workspace HTML file for display in the LAN UI (returns ARTIFACT tag)."""
        name = Path(filename).name
        if not name.endswith(".html"):
            return "Only .html artifacts can be registered."
        try:
            path = resolve_for_root(
                "workspace",
                name,
                ingest_root,
                workspace_root,
                must_exist=True,
            )
        except PathViolationError as exc:
            return str(exc)
        if not path.is_file():
            return "File not found."
        return f"ARTIFACT:{name}"

    tool_map = {
        "ingest_scan": ingest_scan,
        "rag_search": rag_search,
        "extract_structured": extract_structured,
        "write_html_artifact": write_html_artifact,
        "register_artifact": register_artifact,
    }

    for t in make_fs_tools(settings):
        tool_map[t.name] = t
    for t in make_script_tools(settings):
        tool_map[t.name] = t

    enabled = profile.get("tools")
    if enabled:
        missing = [n for n in enabled if n not in tool_map]
        if missing:
            raise RuntimeError(f"Unknown tools in profile config: {missing}")
        return [tool_map[n] for n in enabled]

    return list(tool_map.values())
