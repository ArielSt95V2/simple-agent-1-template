# Document chatbot (example profile)

Default profile for the LAN agent template (`AGENT_PROFILE=document-chatbot`).

## Behavior (target)

1. Operators copy uploads into the host **ingest** folder (`data/ingest` by default).
2. Agent scans `/ingest`, chunks and embeds into Postgres (pgvector).
3. Chat uses RAG + LangGraph state. The thread (messages, tool calls, approval pauses) is checkpointed in Postgres. The agent can generate HTML under `/workspace`.
4. UI loads artifacts via `/api/artifacts/{name}` in a sandboxed iframe.

## Customize

Edit `config.yaml` (tools list, RAG params, HITL flags). For a different agent variant, copy this folder under `examples/` and set `AGENT_PROFILE`.
