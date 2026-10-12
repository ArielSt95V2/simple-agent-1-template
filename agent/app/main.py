from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent.app.chat import ingest_only, invoke_chat, resume_chat
from agent.app.config import get_settings, load_agent_profile
from agent.app.runtime import AgentRuntime, create_runtime

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ingest_path.mkdir(parents=True, exist_ok=True)
    settings.workspace_path.mkdir(parents=True, exist_ok=True)

    app.state.runtime = None
    app.state.runtime_error = None
    try:
        app.state.runtime = create_runtime(settings)
    except Exception as exc:
        app.state.runtime_error = str(exc)

    try:
        yield
    finally:
        runtime = app.state.runtime
        if runtime is not None:
            runtime.close()


app = FastAPI(title="LAN Agent Template", version="0.3.0", lifespan=lifespan)


def _runtime(app: FastAPI) -> AgentRuntime:
    if app.state.runtime is None:
        detail = app.state.runtime_error or "Agent runtime not initialized"
        raise HTTPException(status_code=503, detail=detail)
    return app.state.runtime


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok" if app.state.runtime else "degraded",
        "runtime": app.state.runtime is not None,
        "detail": app.state.runtime_error,
        "profile": settings.agent_profile,
    }


@app.get("/api/config")
def api_config() -> dict:
    settings = get_settings()
    profile = load_agent_profile(settings)
    return {
        "profile": settings.agent_profile,
        "ingest_path": str(settings.ingest_path),
        "workspace_path": str(settings.workspace_path),
        "profile_config": profile,
        "runtime_ready": app.state.runtime is not None,
    }


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool = Field(default=True)


@app.post("/api/chat")
def chat(body: ChatRequest) -> dict:
    runtime = _runtime(app)
    thread_id = body.thread_id or "default"
    return invoke_chat(runtime, body.message, thread_id)


@app.post("/api/chat/resume")
def chat_resume(body: ResumeRequest) -> dict:
    runtime = _runtime(app)
    return resume_chat(runtime, body.thread_id, body.approved)


@app.post("/api/ingest")
def ingest() -> dict:
    runtime = _runtime(app)
    return ingest_only(runtime)


@app.get("/api/artifacts")
def list_artifacts() -> dict:
    settings = get_settings()
    root = settings.workspace_path.resolve()
    if not root.is_dir():
        return {"artifacts": []}
    names = sorted(
        p.name for p in root.glob("*.html") if p.is_file() and p.stat().st_size <= 5_000_000
    )
    return {"artifacts": names}


@app.get("/api/artifacts/{name}")
def get_artifact(name: str):
    settings = get_settings()
    path = (settings.workspace_path / name).resolve()
    root = settings.workspace_path.resolve()
    if not str(path).startswith(str(root)) or not path.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(path, media_type="text/html")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "agent.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
