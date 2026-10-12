import subprocess

from langchain_core.tools import tool

from agent.app.config import Settings
from agent.sandbox.paths import PathViolationError, resolve_for_root
from agent.sandbox.runner import run_workspace_script


def make_script_tools(settings: Settings) -> list:
    ingest_root = settings.ingest_path
    workspace_root = settings.workspace_path

    @tool
    def run_script(relative_path: str) -> str:
        """Run a .py, .sh, or .js script from workspace (e.g. transform CSV before HTML)."""
        try:
            path = resolve_for_root(
                "workspace",
                relative_path,
                ingest_root,
                workspace_root,
                must_exist=True,
            )
            return run_workspace_script(
                path,
                workspace_root,
                timeout_seconds=settings.script_timeout_seconds,
                max_output_chars=settings.max_tool_output_chars,
            )
        except PathViolationError as exc:
            return str(exc)
        except subprocess.TimeoutExpired:
            return f"Script timed out after {settings.script_timeout_seconds}s."
        except ValueError as exc:
            return str(exc)

    return [run_script]
