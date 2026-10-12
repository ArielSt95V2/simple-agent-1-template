# Reusing this template

Short guide for developers who clone this repo and want a **new agent variant** without rebuilding Docker, LangGraph, or the UI from scratch.

**Idea:** one shared **sandbox image** and **Compose stack**; each project differs mainly by **profile** (`examples/<name>/config.yaml`), **prompt/graph** code, and **tool list**.

---

## 1. Fast path (new agent in 15 minutes)

```text
1. Clone the template
2. Copy examples/document-chatbot/ → examples/my-agent/
3. Edit examples/my-agent/config.yaml (tools, RAG, HITL)
4. Set AGENT_PROFILE=my-agent in compose/.env
5. Tweak SYSTEM_PROMPT in agent/graph/react.py (or add a new graph module)
6. docker compose up --build
```

---

## 2. Variants: what to change

| Layer | Where | When to change |
|--------|--------|----------------|
| **Prompts** | `agent/graph/react.py` → `SYSTEM_PROMPT`, or load from `examples/<profile>/prompt.md` (optional pattern) | Tone, workflow steps, HTML/chart rules |
| **Tools** | `examples/<profile>/config.yaml` → `tools:` list; implement in `agent/tools/` and register in `agent/tools/registry.py` | Different capabilities per agent |
| **Graph** | `agent/graph/react.py` (ReAct today); add `agent/graph/my_graph.py` for non-ReAct | Different control flow, extra nodes, HITL |
| **Sandbox image** | Usually **unchanged** — one `sandbox/Dockerfile` for all variants | Only if you need extra OS packages (e.g. `pandoc`, `R`) |

You do **not** need a new Docker image for a new prompt or tool list — only rebuild when `sandbox/Dockerfile` or Python dependencies change.

---

## 3. Configuration format

Two layers (keep both small):

### `.env` (secrets & infrastructure)

Location: `compose/.env` (copy from `compose/.env.example`).

| Variable | Purpose |
|----------|---------|
| `AGENT_PROFILE` | Folder name under `examples/` |
| `OPENAI_API_KEY` | Default LLM |
| `POSTGRES_URL` | RAG embeddings and chat checkpoints (separate tables) |
| `INGEST_HOST_PATH` / `WORKSPACE_HOST_PATH` | LAN folders on the host |

### `config.yaml` (agent behavior)

Location: `examples/<profile>/config.yaml`.

Minimal shape:

```yaml
name: my-agent
description: One line for your team.

graph: react   # today only "react" is wired; extend in agent/graph/

tools:
  - ingest_scan
  - rag_search
  - write_html_artifact

hitl:
  enabled: false

rag:
  chunk_size: 1000
  chunk_overlap: 150

artifacts:
  default_filename: report.html
```

**Rule:** every name under `tools:` must exist in `agent/tools/registry.py` → `tool_map`. Unknown names fail at startup with a clear error.

---

## 4. Example agents

### Default: `document-chatbot`

- RAG from `/ingest`, HTML artifacts, HITL on publish.
- See [examples/document-chatbot/README.md](../examples/document-chatbot/README.md).

### Add a second example (pattern)

```text
examples/
  document-chatbot/
  ops-dashboard/          ← copy from document-chatbot
    config.yaml
    README.md
```

Example `ops-dashboard/config.yaml` diff:

```yaml
name: ops-dashboard
description: Shorter RAG answers; no HITL; fewer tools.

tools:
  - ingest_scan
  - rag_search
  - read_file
  - write_html_artifact

hitl:
  enabled: false

artifacts:
  default_filename: dashboard.html
```

Then in `compose/.env`:

```env
AGENT_PROFILE=ops-dashboard
```

Switch profiles by changing `AGENT_PROFILE` and restarting the agent container — same image, same Postgres.

---

## 5. Tool style (LangChain `@tool`)

All tools are **plain LangChain tools**, not MCP.

| Step | Action |
|------|--------|
| 1 | Add a function in `agent/tools/` (or extend `fs_tools.py` / `script_tools.py`) |
| 2 | Decorate with `@tool` and a clear docstring (the model reads it) |
| 3 | Register the tool **name** (function name) in `build_tools()` → `tool_map` |
| 4 | Add the name to your profile `config.yaml` → `tools:` |

**Minimal new tool example:**

```python
# agent/tools/my_tools.py
from langchain_core.tools import tool

@tool
def ping_service(host: str) -> str:
    """Check if a host responds on the LAN (example stub)."""
    return f"Would ping {host} (implement me)."
```

```python
# agent/tools/registry.py — inside build_tools(), before tool_map is built:
from agent.tools.my_tools import ping_service
# ...
tool_map["ping_service"] = ping_service
```

```yaml
# examples/my-agent/config.yaml
tools:
  - rag_search
  - ping_service
```

**Sandbox rules:** file paths use `agent/sandbox/paths.py` — ingest is read-only in Compose; writes and scripts only under `/workspace`.

---

## 6. Sandbox image (one image, many agents)

| File | Role |
|------|------|
| `sandbox/Dockerfile` | Python 3.12, Node, git, non-root user |
| `sandbox/entrypoint.sh` | Ensures `/workspace/scripts`, starts `lan-agent` |
| `compose/docker-compose.yml` | Binds ingest (ro), workspace (rw), port 8080 |

**When to edit the Dockerfile**

- Install system deps: `apt-get install …` in `sandbox/Dockerfile`
- Add Python deps: `pyproject.toml` → rebuild image

**When not to edit**

- New agent profile, prompt, or tool list only → restart container, no Dockerfile change.

**LAN ingest share:** `compose/docker-compose.lan.example.yml` or set `INGEST_HOST_PATH` in `.env`. Details: [SANDBOX.md](./SANDBOX.md).

---

## 7. Graph variants (beyond ReAct)

Today: `build_compiled_graph()` in `agent/graph/react.py` uses `create_react_agent`. The app opens one Postgres connection pool at startup and passes it in, so chat checkpoints stay in Postgres.

To add a custom graph:

1. Add `agent/graph/ops_dashboard.py` with `build_compiled_graph(settings, profile, checkpoint_pool)`.
2. In `agent/app/runtime.py`, branch on `profile.get("graph")` and pass the same pool:

```python
graph_kind = profile.get("graph", "react")
if graph_kind == "react":
    graph = build_react_graph(settings, profile, pool)
elif graph_kind == "ops":
    graph = build_ops_graph(settings, profile, pool)
```

3. Set `graph: ops` in `config.yaml`.

Keep one graph module per variant until shared nodes are worth extracting.

---

## 8. Checklist before you ship a new variant

- [ ] `examples/<name>/config.yaml` + short README
- [ ] `AGENT_PROFILE=<name>` in `compose/.env`
- [ ] All `tools:` registered in `registry.py`
- [ ] Prompt/graph updated for the use case
- [ ] Smoke test: [MANUAL_VERIFICATION.md](./MANUAL_VERIFICATION.md)
- [ ] Secrets only in `.env`, not in YAML

---

## 9. Publish as a git template (you do this manually)

On your remote (GitHub/GitLab/etc.):

1. Push this repo once as **`lan-agent-template`** (or similar).
2. Enable **Template repository** in repo settings (GitHub: Settings → Template repository).
3. New projects: **Use this template** → clone → rename → set `AGENT_PROFILE` and `.env`.

Optional tag releases (`v0.3.0`) so teams can pin `git clone -b v0.3.0 …`.

No code changes required in the template for that workflow — only remote settings and docs.
