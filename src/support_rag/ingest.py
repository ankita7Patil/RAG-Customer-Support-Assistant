from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .config import AppConfig

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None
    embedding_functions = None


WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def normalize_token(token: str) -> str:
    token = token.lower()
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    text: str
    source: str
    page_number: int


class SimpleVectorStore:
    """Fallback local store used when ChromaDB is unavailable."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._items: list[dict] = []
        if self.store_path.exists():
            self._items = json.loads(self.store_path.read_text(encoding="utf-8"))

    def add(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._items.append(
                {
                    "id": chunk.chunk_id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "page_number": chunk.page_number,
                    "vector": self._vectorize(chunk.text),
                }
            )
        self.store_path.write_text(json.dumps(self._items, indent=2), encoding="utf-8")

    def search(self, query: str, top_k: int) -> list[dict]:
        query_vector = self._vectorize(query)
        scored = []
        for item in self._items:
            score = self._cosine_similarity(query_vector, item["vector"])
            scored.append(
                {
                    "id": item["id"],
                    "text": item["text"],
                    "source": item["source"],
                    "page_number": item["page_number"],
                    "score": round(score, 4),
                }
            )
        return sorted(scored, key=lambda value: value["score"], reverse=True)[:top_k]

    @staticmethod
    def _vectorize(text: str) -> dict[str, float]:
        tokens = [normalize_token(token) for token in WORD_RE.findall(text)]
        counts = Counter(tokens)
        total = sum(counts.values()) or 1
        return {token: count / total for token, count in counts.items()}

    @staticmethod
    def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
        shared = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in shared)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        denominator = left_norm * right_norm
        return numerator / denominator if denominator else 0.0


def load_pdf_chunks(pdf_path: Path, config: AppConfig) -> list[Chunk]:
    reader = PdfReader(str(pdf_path))
    chunks: list[Chunk] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        for chunk_index, chunk_text in enumerate(
            split_text(text, config.chunk_size, config.chunk_overlap), start=1
        ):
            chunks.append(
                Chunk(
                    chunk_id=f"{pdf_path.stem}-p{page_index}-c{chunk_index}",
                    text=chunk_text,
                    source=pdf_path.name,
                    page_number=page_index,
                )
            )
    return chunks


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def ingest_pdf(pdf_path: Path, config: AppConfig) -> int:
    chunks = load_pdf_chunks(pdf_path, config)
    if chromadb and embedding_functions:
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_or_create_collection(
            name=config.collection_name,
            embedding_function=embedding_fn,
        )
        collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {"source": chunk.source, "page_number": chunk.page_number}
                for chunk in chunks
            ],
        )
    else:
        store = SimpleVectorStore(config.chroma_dir / "fallback_store.json")
        store.add(chunks)
    return len(chunks)
