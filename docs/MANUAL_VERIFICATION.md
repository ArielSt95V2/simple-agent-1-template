# Manual verification (Postman, curl, browser)

Run after `docker compose up --build` from `compose/` with a valid `compose/.env`.

Replace `HOST` with `localhost` or your LAN IP (e.g. `192.168.1.50`).

Base URL: `http://HOST:8080`

---

## 1. Health & config

| Check | Method | URL | Expected |
|-------|--------|-----|----------|
| Liveness | GET | `/health` | `200`, `"status": "ok"`, `"runtime": true` |
| Profile | GET | `/api/config` | `200`, your `AGENT_PROFILE`, paths `/ingest`, `/workspace` |

**curl**

```bash
curl -s http://HOST:8080/health | jq
curl -s http://HOST:8080/api/config | jq
```

**Postman**

- Import **`postman/LAN-Agent-Template.postman_collection.json`** and **`postman/LAN-Agent-Template.postman_environment.json`**.
- Run folder **0 — Smoke (run in order)**. See [postman/README.md](../postman/README.md).
- No auth headers in v1.

If `"runtime": false`, read `"detail"` in `/health` (often missing `OPENAI_API_KEY` or Postgres).

---

## 2. Ingest & RAG (optional but recommended)

1. Copy a small `.md` or `.txt` file into host `data/ingest/`.
2. **POST** `/api/ingest` — no body.

```bash
curl -s -X POST http://HOST:8080/api/ingest | jq
```

Expect JSON with `ingested_files` ≥ 0 or `skipped` if unchanged.

---

## 3. Chat (stub flow → full agent)

**POST** `/api/chat`

Headers: `Content-Type: application/json`

Body:

```json
{
  "message": "Run ingest_scan and summarize what is in the documents.",
  "thread_id": "postman-test-1"
}
```

Expect `200`, `"status": "ok"`, non-empty `"reply"`, `"thread_id"` echoed.

Repeat with the same `thread_id` to exercise Postgres chat checkpoints.

---

## 4. HTML artifact (if the model writes one)

**GET** `/api/artifacts` → list of `.html` names.

**GET** `/api/artifacts/summary.html` → `200`, `text/html`.

Browser: open `http://HOST:8080/` — chat UI + iframe.

---

## 5. HITL resume (if interrupt)

When chat returns `"status": "interrupt"`:

**POST** `/api/chat/resume`

```json
{
  "thread_id": "postman-test-1",
  "approved": true
}
```

Then **GET** `/api/artifacts/<filename>` if `"artifact_url"` was returned.

---

## 6. Docker-level health

```bash
docker compose ps
docker inspect --format='{{.State.Health.Status}}' compose-agent-1
```

Container health should become `healthy` once `/health` succeeds inside the image.

---

## 7. LAN check (second machine)

From another PC on the network:

- `http://<agent-host-ip>:8080/health`
- Open the chat UI in a browser

Ensure host firewall allows inbound **8080** on the agent PC.

---

## 8. Quick pass/fail

| Step | Pass |
|------|------|
| `/health` runtime true | Stack + OpenAI key OK |
| `/api/ingest` | Mount `/ingest` + Postgres OK |
| `/api/chat` | LangGraph + Postgres checkpoints OK |
| UI loads | Static files OK |
| `/api/artifacts/...` | Workspace mount OK |

When all pass, the template is ready to publish as a **git template** on your remote.
