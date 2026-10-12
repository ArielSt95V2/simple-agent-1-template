# Security checklist (v1 — trusted LAN)

This template assumes a **private LAN** with **no authentication**. Do not expose port `8080` to the public internet without hardening (Phase 6).

## Before first run

- [ ] Copy `compose/.env.example` → `compose/.env`; never commit `.env`
- [ ] Set a strong `POSTGRES_PASSWORD`
- [ ] Restrict Windows/Linux firewall to LAN subnets for port `8080`
- [x] Ingest mount is **read-only** (`:ro`) in default `docker-compose.yml`

## Secrets

- `OPENAI_API_KEY` only in `.env` or host secret store
- No API keys in `config.yaml` or chat logs

## HTML artifacts

- UI uses iframe `sandbox="allow-scripts allow-same-origin"` — review before widening permissions
- Serve artifacts only from `/workspace`; path traversal blocked in `/api/artifacts/{name}`

## Data

- Uploaded files may contain sensitive content; Postgres holds embeddings of those files and the chat checkpoints (messages, tool calls, approval pauses)
- Plan retention and backup for `data/ingest`, `data/workspace`, and Docker volumes

## Later (Phase 6)

- API auth, audit logs, command allowlists, resource limits
