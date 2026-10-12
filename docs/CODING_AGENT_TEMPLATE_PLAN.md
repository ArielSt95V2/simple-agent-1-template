# Coding Agent Template — Plan

> Status: **v0.8 — Phase 5 reuse docs complete; manual verify + git template on you**  
> Stack: LangChain + LangGraph · Runtime: Docker (sandbox) · Network: LAN

## 1. Purpose

Reusable **git template** for a **LAN chatbot agent** (LangGraph + LangChain) that:

1. **Ingests files** from a **fixed upload path** on the network (drop folder on a designated PC),
2. **Embeds and queries** content via **Postgres (pgvector)** and/or **extracts** structured information for context,
3. **Chats** with users over HTTP on the LAN,
4. **Publishes HTML artifacts** — interactive summaries with diagrams and charts — shown in a **sandboxed iframe** in the UI.

**v1:** **one agent** / one agent container on the host (no multi-agent Compose profile yet).

## 2. Principles

- **Simplest vertical slice first** — add Postgres, RAG, and HITL hooks only as needed for the first working demo.
- **Sandbox by default:** file I/O and scripts run **inside** the agent container, not on the host PC.
- **One sandbox per agent (model)** — v1 runs **a single agent instance**; template still supports “one container per agent type” when you add variants later.
- **Graph-first:** agent behavior and context live in **LangGraph state**; keep the initial graph small.
- **LAN-only exposure:** one designated PC hosts the stack; clients use a **URL on the local network** (no auth in v1).
- **Template, not product:** empty repo to clone, one example agent, extend via prompts / tools / graphs.

## 3. Target architecture (v1, simple)

```text
[LAN users] → upload/copy files → [Fixed ingest path on file/DB PC]
                                              ↓ (bind mount or sync)
[Browser on LAN] → HTTP :8080 (chat + sandboxed iframe for HTML)
                         ↓
         [Agent container: LangGraph + LangChain @tool + OpenAI]
                    ↓
            [Postgres+pgvector]
         embeddings + chat checkpoints
                    ↓
              /workspace (artifacts .html, scripts)
                         ↓
              [OpenAI API via LangChain] (default LLM)
```

**Mounts (clarification):**

- **`/workspace`** — agent read/write for generated HTML and scratch files.
- **`/ingest`** (name TBD in compose) — **read-only or RW bind** to the **fixed LAN upload directory** on the database/file PC so the agent can watch, parse, and embed new files into Postgres.

Devcontainer support is **deferred**.

## 4. Decisions summary

| Topic | Decision |
|--------|----------|
| Agent capabilities | Read/write files; run **scripts in sandbox** to support HTML artifacts; produce **interactive HTML** (dashboards, summaries, diagrams) |
| Sandboxing | **One container per agent** (LangGraph runs **in that container**) |
| Host deployment | **One PC** on the LAN runs Docker Compose; service reachable by **URL** |
| LLM (default) | **OpenAI** through **LangChain** (`ChatOpenAI` / LangChain integration); other providers optional later |
| LLM access | API keys in **`.env`** on the agent host; orchestrator calls OpenAI over the internet |
| First agent | **Chatbot:** ingest from fixed path → embed/extract → RAG context → **HTML artifact** (summary, charts, diagrams) |
| RAG source | Files placed in a **fixed path on the LAN** (e.g. share on the “database” PC); pipeline embeds into Postgres |
| Multi-agent | **No** in v1 — single agent service only |
| HTML in UI | **Sandboxed iframe** (`sandbox` attribute) — approved |
| Graph | **ReAct** loop (minimal nodes) |
| HITL | **Minimal configurable** hook (learn workflow; not heavy gating in v1) |
| Checkpoints | **Postgres** (LangGraph `PostgresSaver`; own tables, same database as RAG) |
| RAG / embeddings | **Postgres** with pgvector (simple RAG in chat) |
| Context | Primarily **LangGraph state**; RAG supplements chat |
| UI | **Web chatbot** + in-app **HTML preview** (browser-like pane) |
| HTTP API | **Yes** (same app serves UI + API) |
| Compose | **One agent container + Postgres** (Postgres may run on same PC or LAN-visible DB host) |
| Port | **`8080`** (document in README; change via env if needed) |
| Auth | **None** (trusted LAN only) |
| Variants | Different **prompts, tools, and graphs** |
| Config | **`.env` + `config.yaml`** (agent registry / profiles — keep tiny) |
| Tools | **LangChain `@tool`** callables (not MCP) |
| Sandbox image | **Single shared Dockerfile** for all variants |
| Package mgr | **`uv`** (stdlib-compatible; `pip` still works in Docker) |
| Python | **`>=3.12`** orchestrator |
| Ship as | **Git template** (clone and customize) |
| Limits / hardening / Phase 6 | **Later** |

## 5. Phases

---

### Phase 0 — Decisions

**Questions**

1. What should the **first coding agent** be allowed to do in the sandbox?
2. **One sandbox per task** or **per agent/session**?
3. **Network exposure**
4. **Internet / egress**
5. **LLM and secrets**

**Your answers**

| # | Answer |
|---|--------|
| 1 | Read/write files; run scripts in sandbox; create **HTML artifacts** (dashboards, summaries, data-flow diagrams) for display in the UI |
| 2 | **One sandbox per agent** — each agent has its own sandbox |
| 3 | Exposed on **LAN** only (not public internet); hosted on one PC, accessed via URL |
| 4 | **LLM calls** to **OpenAI** (default) via LangChain; sandbox focused on files/scripts |
| 5 | **`OPENAI_API_KEY`** (and related) via **environment** on the host/Compose (`.env`, not committed) |

**Checklist**

- [x] Agent capabilities locked
- [x] Sandbox image strategy chosen (shared project Dockerfile)
- [x] Network and egress policy chosen
- [x] LLM provider and secrets approach chosen (multi-provider via LangChain; keys in env)
- [x] Persistence chosen (**Postgres** for embeddings/RAG and for chat checkpoints)

---

### Phase 1 — Plan & repo skeleton

**Questions**

1. Orchestrator language and minimum version?
2. Repo layout?
3. Package manager?
4. Distribution?
5. Documentation bar?

**Your answers**

| # | Answer |
|---|--------|
| 1 | **Python `>=3.12`** orchestrator (LangGraph/LangChain) |
| 2 | `agent/` + `sandbox/` + `compose/` + **`examples/`** (+ `docs/`) |
| 3 | **`uv`** preferred (template still pip-friendly in Docker) |
| 4 | **Git template** — empty starter to clone and adjust |
| 5 | **Simple:** README + short quickstart (no heavy ADR folder in v1) |

**Checklist**

- [x] Repo layout agreed
- [x] ADR process (if any) — skip for v1
- [x] `.env.example` and security checklist (`compose/.env.example`, `docs/SECURITY.md`)
- [ ] License / naming for the template repo (optional MIT — add when publishing)
- [x] Minimum docs (README + `docs/QUICKSTART.md`)

**Proposed layout (minimal)**

```text
agent/           # LangGraph app, tools, API + chat UI
sandbox/         # Dockerfile (shared), entrypoint
compose/         # docker-compose.yml, .env.example
examples/        # first sample agent config
docs/            # this plan + quick notes
```

---

### Phase 2 — Minimal LangGraph agent

**Questions**

1. Graph shape?
2. Human-in-the-loop?
3. Checkpointing?
4. Context?
5. Interface?

**Your answers**

| # | Answer |
|---|--------|
| 1 | **ReAct** shape (think → tool → repeat); keep initial graph **small** |
| 2 | **Minimal HITL** configuration wired in so we can see it in the workflow |
| 3 | **Checkpoints yes.** **Postgres** stores chat checkpoints and embeddings in one database, separate tables. A connection pool of 10 covers overlapping chats. |
| 4 | Context driven by **LangGraph state**; **simple RAG** in chat; refine shape later |
| 5 | **Web chatbot** with **HTML artifact viewer** (not CLI-first) |

**Checklist**

- [x] State schema (`agent/graph/state.py` + ReAct message state)
- [x] Core ReAct graph (`create_react_agent` in `agent/graph/react.py`)
- [x] LLM + `@tool` wiring (`agent/tools/registry.py`)
- [x] Web UI + API (`/api/chat`, `/api/chat/resume`, `/api/ingest`)
- [x] Postgres checkpoints + minimal HITL on `write_html_artifact`

**Example agent (v1):** **Document chatbot** — ingest from fixed LAN upload path → Postgres embeddings + extraction → chat → generate **interactive HTML summary** (charts/diagrams) in iframe. Config lives under `examples/document-chatbot/` (name TBD when scaffolding).

---

### Phase 3 — Docker sandbox

**Questions**

1. Integration pattern?
2. Base image?
3. Workspace mounts?
4. Toolchain?
5. Limits?

**Your answers**

| # | Answer |
|---|--------|
| 1 | **LangGraph + agent in one container** per agent |
| 2 | **Project `sandbox/Dockerfile`** for v1; **devcontainer** decision later |
| 3 | *(Clarified)* Use a per-agent **`/workspace`** mount (RW) for files and HTML output — not “which PC” (that PC is the single LAN host) |
| 4 | **Standard toolchain OK** in sandbox (git, python, node as needed for scripts/HTML) |
| 5 | **No resource limits in v1** |

**Checklist**

- [x] Base image and non-root user + Node/git/bash (`sandbox/Dockerfile`)
- [x] Volume mount rules — `/ingest:ro`, `/workspace:rw` + env host paths
- [x] Tools: `read_file`, `write_file`, `list_files`, `run_script`, `register_artifact`
- [x] Soft limits (`SCRIPT_TIMEOUT_SECONDS`, read/write size caps); Docker CPU/mem deferred
- [x] Integration pattern (graph in container) + `docs/SANDBOX.md`

---

### Phase 4 — Local network integration

**Questions**

1. HTTP API?
2. Compose services?
3. Ports?
4. Callers?
5. Auth?

**Your answers**

| # | Answer |
|---|--------|
| 1 | **Include HTTP API** (v1) |
| 2 | **Orchestrator + sandbox image + Postgres** (RAG embeddings and chat checkpoints) |
| 3 | **Port `8080`** (template default; override via env) |
| 4 | **LAN clients** (browsers on other machines on the network) |
| 5 | **No authentication** for now |

**Checklist**

- [x] Client surfaces (web UI + HTTP API)
- [x] Compose topology
- [x] Ports and LAN exposure (`0.0.0.0:8080` on host — document firewall)
- [x] Health checks (`/health` + Docker HEALTHCHECK) — verify manually: [MANUAL_VERIFICATION.md](./MANUAL_VERIFICATION.md)
- [x] Auth for network API (none v1)

---

### Phase 5 — Reusability & variants

**Questions**

1. How variants differ?
2. Configuration format?
3. Example agents?
4. Tool style?
5. Sandbox images?

**Your answers**

| # | Answer |
|---|--------|
| 1 | **Prompts, tools, and graphs** |
| 2 | **`.env` + `config.yaml`** (template default — small agent registry) |
| 3 | **One example:** document/RAG chatbot with HTML artifacts (see Phase 2); second variant later |
| 4 | **LangChain `@tool`** callables (**not MCP**) |
| 5 | **One sandbox image** for all variants |

**Checklist**

- [x] Agent profiles / presets in `config.yaml` (`document-chatbot`, `ops-dashboard`)
- [x] Config-driven graph selection (documented; `graph: react` wired)
- [x] Example agents (two profiles under `examples/`)
- [x] Extension points — [REUSE_TEMPLATE.md](./REUSE_TEMPLATE.md)
- [x] Versioning — tag releases when publishing git template (manual)

---

### Phase 6 — Hardening (later)

**Questions**

1.–5. **Deferred** — decide when first demo works on LAN.

**Your answers**

| # | Answer |
|---|--------|
| 1–5 | *TBD after v1 demo* |

**Checklist**

- [ ] Human approval gates (expand beyond minimal HITL)
- [ ] Audit logging
- [ ] CI pipeline
- [ ] Threat model
- [ ] Operational runbook

---

## 6. Resolved product choices

| # | Question | Answer |
|---|----------|--------|
| 1 | First agent purpose | Chatbot: **local DB + embed/extract from files** → context → **HTML artifact** (interactive summary, diagrams, charts) |
| 2 | Default LLM | **OpenAI** via **LangChain** |
| 3 | RAG / file source | **Upload to fixed path** on LAN (file/“database” PC); ingest into Postgres |
| 4 | Multi-agent | **No** — single agent in v1 |
| 5 | HTML display | **Sandboxed iframe** in UI |

**Optional later (not blocking v1):** exact UNC/SMB path or host IP for ingest mount; whether Postgres runs on the same PC as uploads or only the agent host connects over LAN.

## 7. Suggested implementation order (keep it simple)

1. `compose/` + `sandbox/Dockerfile` + `agent/` — LAN `:8080`, `/health`
2. Postgres + pgvector; **ingest job/tool** reads fixed **`INGEST_PATH`** mount → chunk → embed
3. ReAct graph + OpenAI + RAG retrieval tool
4. Tools: write HTML artifact → UI serves file → **sandbox iframe**
5. Postgres checkpoints + thread resume in chat UI
6. Minimal HITL interrupt (one optional approve step)
7. `examples/document-chatbot/` + git template README (ingest path + OpenAI env documented)

## 8. Changelog

| Version | Notes |
|---------|--------|
| v0.1 | Initial plan structure |
| v0.2 | Questions per phase |
| v0.3 | User answers recorded; simplicity + architecture updated |
| v0.4 | Example agent, OpenAI default, LAN ingest path, iframe UI, single-agent v1 |
| v0.5 | Phase 1 repo skeleton (`agent/`, `sandbox/`, `compose/`, `examples/`, `data/`) |
| v0.6 | Phase 2: ReAct, RAG ingest, Redis checkpoints, HITL, artifact UI |
| v0.7 | Phase 3: sandbox paths, script runner, ro ingest mount, LAN compose example |
| v0.8 | Phase 5: REUSE_TEMPLATE.md, MANUAL_VERIFICATION.md, ops-dashboard example |
| v0.9 | Chat checkpoints moved from Redis to Postgres (`PostgresSaver`, pool size 10). Redis service removed. |
