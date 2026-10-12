# LAN Agent Template

Git template for a **single LAN chatbot agent**: LangGraph + LangChain, Docker, Postgres (pgvector RAG and chat checkpoints), OpenAI, and **HTML artifacts** in a sandboxed iframe.

**Status:** Phase 3 — sandbox mounts (ro ingest / rw workspace), fs + script tools, LAN compose helpers.

## Layout

| Path | Purpose |
|------|---------|
| `agent/` | FastAPI app, static chat UI, graph & tools packages |
| `sandbox/` | Shared agent `Dockerfile` + entrypoint |
| `compose/` | `docker-compose.yml`, `.env.example` |
| `examples/document-chatbot/` | Default agent profile (`config.yaml`) |
| `data/ingest/` | LAN upload drop folder (bind mount) |
| `data/workspace/` | Generated HTML and scratch files |
| `docs/` | Plan, quickstart, security |

## Quick start

```bash
cd compose
cp .env.example .env   # set OPENAI_API_KEY
docker compose up --build
```

Browse `http://<this-pc-lan-ip>:8080`. Details: [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Use as a git template

Clone and rename for each new agent project:

```bash
git clone <this-repo> my-lan-agent
cd my-lan-agent
# adjust examples/, AGENT_PROFILE, prompts/graph in Phase 2+
```

## Local dev

```bash
uv venv && uv pip install -e .
uv run lan-agent
```

Requires Python **≥ 3.12**.

## Docs

- [Implementation plan](docs/CODING_AGENT_TEMPLATE_PLAN.md)
- [Security checklist](docs/SECURITY.md)
- [Sandbox mounts & tools](docs/SANDBOX.md)
- [Reuse template / variants (Phase 5)](docs/REUSE_TEMPLATE.md)
- [Manual verification (Postman / curl)](docs/MANUAL_VERIFICATION.md)
- [Postman collection & environments](postman/README.md)
