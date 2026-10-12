# Postman — LAN Agent Template

## Import

1. Open Postman → **Import** → drag these files:
   - `LAN-Agent-Template.postman_collection.json`
   - `LAN-Agent-Template.postman_environment.json` (localhost)
   - Optional: `LAN-Agent-Template-LAN.postman_environment.json` (edit `host` / `baseUrl` to your agent PC IP)
2. Select environment **LAN Agent — Local** (top-right).
3. Start stack: `cd compose && docker compose up --build`
4. Run collection folder **0 — Smoke (run in order)**.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `baseUrl` | Full origin, e.g. `http://localhost:8080` |
| `threadId` | Chat thread (updated by tests after `/api/chat`) |
| `artifactName` | Last HTML file for `GET /api/artifacts/{{artifactName}}` |
| `agentProfile` | Expected profile name (set from `/health` test) |

For LAN testing, duplicate the environment and set:

```text
baseUrl = http://<agent-pc-ip>:8080
```

## HITL flow

1. Run **Chat — request HTML dashboard** (with `document-chatbot` / HITL on).
2. If response has `"status": "interrupt"`, run **HITL → Resume — Approve artifact**.
3. Run **Artifacts → Get artifact by name**.

## Newman (CLI)

If you install [Postman CLI](https://learning.postman.com/docs/postman-cli/postman-cli-overview/):

```bash
postman collection run postman/LAN-Agent-Template.postman_collection.json \
  -e postman/LAN-Agent-Template.postman_environment.json
```

Chat steps require a valid `OPENAI_API_KEY` and may take 30–60s each.

See also [docs/MANUAL_VERIFICATION.md](../docs/MANUAL_VERIFICATION.md).
