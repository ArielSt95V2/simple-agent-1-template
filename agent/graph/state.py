from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Initial state shape — extend in Phase 2."""

    messages: Annotated[list, add_messages]
    artifact_name: str | None
    rag_context: str | None
