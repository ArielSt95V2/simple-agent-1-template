import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from pathlib import Path

ARTIFACT_RE = re.compile(r"ARTIFACT:(\S+)")
HTML_NAME_RE = re.compile(r"([A-Za-z0-9_.-]+\.html)\b")


def _last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    block.get("text", "") for block in content if isinstance(block, dict)
                )
    return ""


def _artifact_from_messages(messages: list, workspace: Path) -> str | None:
    turn = []
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            break
        turn.append(msg)

    for msg in turn:
        if isinstance(msg, ToolMessage):
            match = ARTIFACT_RE.search(str(msg.content))
            if match:
                return Path(match.group(1)).name

    root = workspace.resolve()
    for msg in turn:
        for name in HTML_NAME_RE.findall(str(getattr(msg, "content", ""))):
            path = (root / name).resolve()
            if str(path).startswith(str(root)) and path.is_file():
                return name
    return None


def _interrupt_payload(snapshot) -> Any | None:
    if not snapshot.interrupts:
        return None
    first = snapshot.interrupts[0]
    return first.value if hasattr(first, "value") else first


def invoke_chat(runtime, message: str, thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    result = runtime.graph.invoke(
        {"messages": [HumanMessage(content=message)]},
        config,
    )
    messages = result.get("messages", [])
    snapshot = runtime.graph.get_state(config)

    interrupt_data = _interrupt_payload(snapshot)
    if interrupt_data is not None:
        return {
            "status": "interrupt",
            "thread_id": thread_id,
            "reply": "Waiting for approval to publish HTML artifact.",
            "interrupt": interrupt_data,
            "artifact_url": None,
        }

    artifact = _artifact_from_messages(
        messages, runtime.settings.workspace_path)
    return {
        "status": "ok",
        "thread_id": thread_id,
        "reply": _last_ai_text(messages) or "Done.",
        "artifact_url": f"/api/artifacts/{artifact}" if artifact else None,
    }


def resume_chat(runtime, thread_id: str, approved: bool) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = runtime.graph.get_state(config)
    if not snapshot.interrupts:
        return {
            "status": "ok",
            "thread_id": thread_id,
            "reply": "No pending approval on this thread.",
            "artifact_url": None,
        }

    resume_value = {"approved": approved} if approved else False
    result = runtime.graph.invoke(Command(resume=resume_value), config)
    messages = result.get("messages", [])
    snapshot = runtime.graph.get_state(config)

    interrupt_data = _interrupt_payload(snapshot)
    if interrupt_data is not None:
        preview = interrupt_data if isinstance(interrupt_data, dict) else {}
        return {
            "status": "interrupt",
            "thread_id": thread_id,
            "reply": preview.get("message", "Still waiting for approval."),
            "interrupt": interrupt_data,
            "artifact_url": None,
        }

    artifact = _artifact_from_messages(
        messages, runtime.settings.workspace_path)
    return {
        "status": "ok",
        "thread_id": thread_id,
        "reply": _last_ai_text(messages) or ("Artifact rejected." if not approved else "Done."),
        "artifact_url": f"/api/artifacts/{artifact}" if artifact else None,
    }


def ingest_only(runtime) -> dict:
    from agent.rag.ingest import ingest_directory
    from agent.rag.store import get_vectorstore

    rag_cfg = runtime.profile.get("rag") or {}
    return ingest_directory(
        runtime.settings.ingest_path,
        get_vectorstore(),
        manifest_dir=runtime.settings.workspace_path,
        chunk_size=int(rag_cfg.get("chunk_size", 1000)),
        chunk_overlap=int(rag_cfg.get("chunk_overlap", 150)),
    )
