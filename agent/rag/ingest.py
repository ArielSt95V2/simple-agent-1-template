import hashlib
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector

TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".html", ".htm", ".py", ".yaml", ".yml"}


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _read_document(path: Path, root: Path) -> Document | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    rel = str(path.relative_to(root))
    return Document(
        page_content=text,
        metadata={"source": rel, "filename": path.name, "path": str(path)},
    )


def ingest_directory(
    ingest_root: Path,
    vectorstore: PGVector,
    *,
    manifest_dir: Path | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> dict:
    ingest_root = ingest_root.resolve()
    if not ingest_root.is_dir():
        return {"ingested_files": 0, "chunks": 0, "skipped": 0, "errors": ["ingest path missing"]}

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    manifest_root = (manifest_dir or ingest_root).resolve()
    manifest_root.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_root / ".ingest_manifest.json"
    manifest: dict[str, str] = {}
    if manifest_path.is_file():
        import json

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}

    ingested_files = 0
    chunks_added = 0
    skipped = 0
    errors: list[str] = []

    for path in sorted(ingest_root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        doc = _read_document(path, ingest_root)
        if doc is None:
            skipped += 1
            continue

        rel = doc.metadata["source"]
        file_hash = _file_hash(path)
        if manifest.get(rel) == file_hash:
            skipped += 1
            continue

        try:
            vectorstore.delete(filter={"source": rel})
        except Exception:
            pass

        chunks = splitter.split_documents([doc])
        if not chunks:
            continue

        ids = [f"{rel}::{i}" for i in range(len(chunks))]
        try:
            vectorstore.add_documents(chunks, ids=ids)
        except Exception as exc:
            errors.append(f"{rel}: {exc}")
            continue

        manifest[rel] = file_hash
        ingested_files += 1
        chunks_added += len(chunks)

    import json

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "ingested_files": ingested_files,
        "chunks": chunks_added,
        "skipped": skipped,
        "errors": errors,
    }
