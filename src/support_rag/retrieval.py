from __future__ import annotations

import re
from pathlib import Path

from .config import AppConfig
from .ingest import SimpleVectorStore, normalize_token
from .state import Intent

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None
    embedding_functions = None


WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def detect_intent(query: str) -> Intent:
    lowered = query.lower()
    if any(token in lowered for token in ["refund", "cancel order", "return"]):
        return "refund"
    if any(token in lowered for token in ["error", "bug", "issue", "failed", "login"]):
        return "technical_issue"
    if any(token in lowered for token in ["human", "agent", "representative", "manager"]):
        return "human_request"
    if any(token in lowered for token in ["price", "delivery", "shipping", "policy", "how"]):
        return "faq"
    return "unknown"


def retrieve_context(query: str, config: AppConfig) -> list[dict]:
    if chromadb and embedding_functions:
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_collection(
            name=config.collection_name,
            embedding_function=embedding_fn,
        )
        results = collection.query(query_texts=[query], n_results=config.top_k)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        chunks = []
        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 1.0
            chunks.append(
                {
                    "id": f"result-{index}",
                    "text": document,
                    "source": metadata.get("source", "unknown"),
                    "page_number": metadata.get("page_number", 0),
                    "score": round(max(0.0, 1.0 - float(distance)), 4),
                }
            )
        return chunks

    store = SimpleVectorStore(Path(config.chroma_dir) / "fallback_store.json")
    return store.search(query, top_k=config.top_k)


def build_answer(query: str, retrieved_chunks: list[dict]) -> tuple[str, float]:
    if not retrieved_chunks:
        return (
            "I could not find a relevant answer in the knowledge base. "
            "I recommend escalating this query to a human support agent.",
            0.0,
        )

    best = retrieved_chunks[0]
    query_tokens = {normalize_token(token) for token in WORD_RE.findall(query)}
    chunk_tokens = {normalize_token(token) for token in WORD_RE.findall(best["text"])}
    overlap_ratio = len(query_tokens & chunk_tokens) / max(1, len(query_tokens))
    confidence = min(0.95, max(0.15, (best["score"] * 2.2) + (overlap_ratio * 0.55)))
    snippet = best["text"][:600].strip()
    answer = (
        f"Based on the support knowledge base, here is the best available guidance for your query:\n\n"
        f"{snippet}\n\n"
        f"Source: {best['source']} (page {best['page_number']})"
    )
    return answer, round(confidence, 2)


def should_escalate(intent: Intent, confidence: float, retrieved_chunks: list[dict]) -> tuple[bool, str]:
    if intent == "human_request":
        return True, "Customer explicitly requested a human agent."
    if not retrieved_chunks:
        return True, "No relevant chunks were found in the knowledge base."
    if confidence < 0.45:
        return True, "The retrieval confidence is below the escalation threshold."
    if intent in {"technical_issue", "unknown"} and confidence < 0.6:
        return True, "The query is technical or ambiguous and needs human validation."
    return False, ""
