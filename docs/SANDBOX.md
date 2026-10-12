# Docker sandbox (Phase 3)

The **agent container** runs LangGraph, tools, and the HTTP UI. File and script tools never touch the host filesystem except through Docker bind mounts.

## Mounts

| Container path | Default host path | Mode | Purpose |
|----------------|-------------------|------|---------|
| `/ingest` | `data/ingest` | **read-only** | LAN uploads / shared inbox |
| `/workspace` | `data/workspace` | **read-write** | HTML artifacts, scripts, manifest |

Configure host paths in `compose/.env`:

- `INGEST_HOST_PATH`
- `WORKSPACE_HOST_PATH`

For a UNC/share on Windows, use `compose/docker-compose.lan.example.yml` or set an absolute path in `INGEST_HOST_PATH`.

## Tool boundaries

| Tool | Scope |
|------|--------|
| `read_file`, `list_files`, `extract_structured`, `ingest_scan` | Ingest (read) |
| `write_file`, `run_script`, `write_html_artifact`, `register_artifact` | Workspace only |
| `run_script` | `.py`, `.sh`, `.js` under workspace; subprocess timeout via `SCRIPT_TIMEOUT_SECONDS` |

Paths must be **relative** with no `..` segments (see `agent/sandbox/paths.py`).

## Image contents

- Python 3.12, git, bash, **Node.js** (for optional chart/data scripts)
- Non-root user `agent` (uid 1000)
- `HEALTHCHECK` on `/health`

## Example script

`data/workspace/scripts/example_transform.py` — ask the agent to run:

`run_script('scripts/example_transform.py')`

## Resource limits

Docker CPU/memory caps are **not** set in v1. Soft limits: script timeout and max read/write sizes in `.env`.
