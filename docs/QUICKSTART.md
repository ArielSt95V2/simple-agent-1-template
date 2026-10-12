# Quickstart

## Prerequisites

- Docker Desktop (or Docker Engine) on the **LAN host PC**
- Python **3.12+** and [uv](https://docs.astral.sh/uv/) for local dev (optional)
- OpenAI API key

## Run with Docker (recommended)

```bash
cd compose
cp .env.example .env
# Edit .env: set OPENAI_API_KEY and POSTGRES_PASSWORD

docker compose up --build
```

Open from any machine on the LAN: `http://<host-ip>:8080`

Drop files into `data/ingest` on the host (or bind a network share in `docker-compose.yml`).

## Local dev (no Docker)

```bash
uv venv
uv pip install -e ".[dev]"
export OPENAI_API_KEY=sk-...
uv run lan-agent
```

Postgres and `OPENAI_API_KEY` are required for the agent graph. Chat history is stored in Postgres, in separate tables from the document embeddings.

## Try the agent

1. Copy a `.txt` or `.md` file into `data/ingest/` on the host.
2. Open the chat UI and ask: *“Run ingest and summarize the documents.”*
3. Ask for an **HTML dashboard** — when HITL is enabled, click **Approve** to publish the artifact.

Optional: `POST /api/ingest` to embed files without chatting.

Ingest is mounted **read-only** inside the container; outputs go to **workspace**. See [SANDBOX.md](./SANDBOX.md).

## APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Runtime and dependency status |
| POST | `/api/chat` | `{ "message", "thread_id"? }` |
| POST | `/api/chat/resume` | `{ "thread_id", "approved" }` after HITL interrupt |
| POST | `/api/ingest` | Scan ingest folder → Postgres embeddings |

## Next

See [CODING_AGENT_TEMPLATE_PLAN.md](./CODING_AGENT_TEMPLATE_PLAN.md) — Phase 3+ hardening and LAN ingest mounts.
