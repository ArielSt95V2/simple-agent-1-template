import subprocess
from pathlib import Path

ALLOWED_SCRIPT_SUFFIXES = {".py", ".sh", ".js"}


def run_workspace_script(
    script_path: Path,
    workspace_root: Path,
    *,
    timeout_seconds: int = 120,
    max_output_chars: int = 12_000,
) -> str:
    script_path = script_path.resolve()
    root = workspace_root.resolve()
    if not str(script_path).startswith(str(root)):
        raise ValueError("Script must live under workspace.")

    if not script_path.is_file():
        raise ValueError(f"Script not found: {script_path.name}")

    suffix = script_path.suffix.lower()
    if suffix not in ALLOWED_SCRIPT_SUFFIXES:
        raise ValueError(f"Unsupported script type: {suffix}")

    if suffix == ".py":
        cmd = ["python", str(script_path)]
    elif suffix == ".sh":
        cmd = ["bash", str(script_path)]
    else:
        cmd = ["node", str(script_path)]

    completed = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=max(1, timeout_seconds),
        check=False,
    )

    stdout = (completed.stdout or "")[:max_output_chars]
    stderr = (completed.stderr or "")[: max_output_chars // 4]
    return (
        f"exit_code={completed.returncode}\n"
        f"--- stdout ---\n{stdout}\n"
        f"--- stderr ---\n{stderr}"
    )
