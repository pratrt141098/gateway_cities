import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from google import genai


@dataclass(frozen=True)
class RagDoc:
    id: str
    text: str


def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY (or GOOGLE_API_KEY). Add it to your environment."
        )
    return genai.Client(api_key=api_key)


def _embed(texts: list[str]) -> np.ndarray:
    """
    Returns shape (n, d) float32 embedding matrix.
    """
    c = _client()
    resp = c.models.embed_content(
        model="models/textembedding-gecko@003",
        contents=texts,
    )

    # google-genai returns either a single embedding or a list depending on input.
    embeddings: list[list[float]] = []
    if isinstance(resp, dict):
        # defensive: older shapes
        if "embedding" in resp:
            embeddings = [resp["embedding"]]
        elif "embeddings" in resp:
            embeddings = [e["values"] for e in resp["embeddings"]]
    else:
        # Expected modern shape
        if getattr(resp, "embedding", None) is not None:
            embeddings = [resp.embedding.values]  # type: ignore[attr-defined]
        else:
            embeddings = [e.values for e in resp.embeddings]  # type: ignore[attr-defined]

    mat = np.array(embeddings, dtype=np.float32)
    return mat


def _normalize_rows(mat: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(mat, axis=1, keepdims=True)
    denom = np.where(denom == 0, 1.0, denom)
    return mat / denom


def build_default_docs(metric_help: dict[str, str]) -> list[RagDoc]:
    metric_lines = "\n".join(
        [f"- {k}: {v}" for k, v in sorted(metric_help.items(), key=lambda x: x[0])]
    )
    return [
        RagDoc(
            id="project",
            text=(
                "You are an assistant for a Massachusetts Gateway Cities dashboard.\n"
                "Use ONLY the provided API tool results for numeric claims.\n"
                "All values should be rates/per-capita when applicable.\n"
                'Always include a source line: "Source: American Community Survey 5-year estimates, [years]".'
            ),
        ),
        RagDoc(
            id="available_endpoints",
            text=(
                "Available tools/data:\n"
                "- foreign-born share (latest year)\n"
                "- time series by city for metrics (2010-2024 where available)\n"
                "- country-of-origin counts (latest year) for a city\n"
                "- education, homeownership, employment/income, poverty, median income (latest year)\n"
                "When a user asks for a trend, use the time series tool.\n"
                "When a user asks for 'top origins', use country-of-origin.\n"
                "When user asks for comparisons, compute from tool outputs, do not guess."
            ),
        ),
        RagDoc(
            id="metrics",
            text=("Time series metric keys:\n" + metric_lines),
        ),
        RagDoc(
            id="format",
            text=(
                "When responding, be concise. If unsure, ask a follow-up question.\n"
                "Do not hallucinate city names. Use exact city strings as provided by the data."
            ),
        ),
    ]


class RagIndex:
    def __init__(self, path: Path):
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def save(self, docs: list[RagDoc], embeddings: np.ndarray) -> None:
        payload = {
            "docs": [{"id": d.id, "text": d.text} for d in docs],
            "embeddings": embeddings.astype(float).tolist(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False))

    def load(self) -> tuple[list[RagDoc], np.ndarray]:
        payload = json.loads(self.path.read_text())
        docs = [RagDoc(**d) for d in payload["docs"]]
        emb = np.array(payload["embeddings"], dtype=np.float32)
        return docs, emb


def ensure_index(index: RagIndex, metric_help: dict[str, str]) -> tuple[list[RagDoc], np.ndarray]:
    if index.exists():
        return index.load()
    docs = build_default_docs(metric_help=metric_help)
    emb = _normalize_rows(_embed([d.text for d in docs]))
    index.save(docs, emb)
    return docs, emb


def retrieve(index: RagIndex, query: str, metric_help: dict[str, str], k: int = 4) -> list[RagDoc]:
    # Fallback: for now, skip semantic similarity and just return
    # the core docs. This avoids dependency on embedding model
    # configuration while still giving Gemini useful context.
    docs = build_default_docs(metric_help=metric_help)
    return docs[: max(1, k)]

