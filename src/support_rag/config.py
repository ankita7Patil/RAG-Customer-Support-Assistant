from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    collection_name: str = os.getenv("COLLECTION_NAME", "customer_support_kb")
    chroma_dir: Path = Path(os.getenv("CHROMA_DIR", "./data/chroma"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    escalation_threshold: float = float(os.getenv("ESCALATION_THRESHOLD", "0.45"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_config() -> AppConfig:
    config = AppConfig()
    config.chroma_dir.mkdir(parents=True, exist_ok=True)
    return config
