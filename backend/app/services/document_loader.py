import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from app.core.config import settings


@dataclass
class DocumentChunk:
    id: str
    content: str
    metadata: Dict[str, Any]


def _chunk_text(text: str, max_chars: int = 900) -> List[str]:
    sections = [section.strip() for section in text.split("\n## ") if section.strip()]
    chunks: List[str] = []

    for section in sections:
        if len(section) <= max_chars:
            chunks.append(section)
            continue

        for start in range(0, len(section), max_chars):
            chunks.append(section[start:start + max_chars].strip())

    return [chunk for chunk in chunks if chunk]


def _stable_id(source: Path, content: str, index: int) -> str:
    digest = hashlib.sha256(f"{source}:{index}:{content}".encode("utf-8")).hexdigest()
    return digest[:24]


def _metadata_from_json(source: Path, item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": str(source),
        "exhibition_name": item.get("name") or item.get("title") or "",
        "category": item.get("category") or "",
        "location": item.get("location") or item.get("place") or "",
    }


def _load_markdown(path: Path) -> Iterable[DocumentChunk]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    title = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    chunks = []
    for index, content in enumerate(_chunk_text(text)):
        chunks.append(
            DocumentChunk(
                id=_stable_id(path, content, index),
                content=content,
                metadata={
                    "source": str(path),
                    "exhibition_name": title,
                    "category": "",
                    "location": "",
                },
            )
        )
    return chunks


def _load_json(path: Path) -> Iterable[DocumentChunk]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("exhibitions", [])
    chunks = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        content = "\n".join(
            str(value)
            for key, value in item.items()
            if key not in {"id", "location_x", "location_y"} and value
        )
        if not content.strip():
            continue
        chunks.append(
            DocumentChunk(
                id=_stable_id(path, content, index),
                content=content,
                metadata=_metadata_from_json(path, item),
            )
        )
    return chunks


def load_documents(data_dir: str = None) -> List[DocumentChunk]:
    root = Path(data_dir or settings.RAG_DATA_DIR)
    if not root.exists():
        return []

    documents: List[DocumentChunk] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() == ".md":
            documents.extend(_load_markdown(path))
        elif path.suffix.lower() == ".json":
            documents.extend(_load_json(path))
    return documents


def summarize_document_sources(data_dir: str = None) -> Dict[str, Any]:
    root = Path(data_dir or settings.RAG_DATA_DIR)
    if not root.exists():
        return {
            "data_dir": str(root),
            "file_count": 0,
            "chunk_count": 0,
            "sources": [],
        }

    sources = []
    chunk_count = 0
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        if path.suffix.lower() == ".md":
            chunks = list(_load_markdown(path))
        else:
            chunks = list(_load_json(path))
        chunk_count += len(chunks)
        sources.append(
            {
                "path": str(path),
                "type": path.suffix.lower().lstrip("."),
                "chunk_count": len(chunks),
            }
        )

    return {
        "data_dir": str(root),
        "file_count": len(sources),
        "chunk_count": chunk_count,
        "sources": sources,
    }
