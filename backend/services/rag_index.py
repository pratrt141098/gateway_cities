from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).parent.parent.parent
FACTS_DIR = BASE_DIR / "data" / "facts"
INDEX_DIR = BASE_DIR / "data" / "rag_index"
INDEX_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RAGDocument:
  text: str
  meta: dict


def _load_fact_files() -> List[RAGDocument]:
  """
  Load all lines from data/facts/*.txt as individual documents.
  """
  docs: List[RAGDocument] = []
  if not FACTS_DIR.exists():
    return docs
  for path in FACTS_DIR.glob("*.txt"):
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
      line = line.strip()
      if not line:
        continue
      docs.append(RAGDocument(text=line, meta={"file": path.name, "line": i + 1}))
  return docs


def build_index() -> None:
  """
  Snapshot the current fact documents into meta.jsonl.
  TF‑IDF vectors will be computed on the fly at query time.
  """
  docs = _load_fact_files()
  if not docs:
    raise RuntimeError("No fact documents found in data/facts. Run scripts/generate_facts.py first.")

  meta_path = INDEX_DIR / "meta.jsonl"
  with meta_path.open("w", encoding="utf-8") as f:
    for d in docs:
      f.write(json.dumps({"text": d.text, "meta": d.meta}, ensure_ascii=False) + "\n")


def load_index() -> List[RAGDocument]:
  meta_path = INDEX_DIR / "meta.jsonl"
  docs: List[RAGDocument] = []
  with meta_path.open("r", encoding="utf-8") as f:
    for line in f:
      obj = json.loads(line)
      docs.append(RAGDocument(text=obj["text"], meta=obj["meta"]))
  return docs


def retrieve(query: str, top_k: int = 5) -> List[RAGDocument]:
  """
  Retrieve top_k fact sentences for a natural-language query using TF‑IDF
  cosine similarity over data/facts/*.txt. Spec: top 5 for verified context.
  """
  docs = load_index()
  if not docs:
    return []
  texts = [d.text for d in docs]
  vectorizer = TfidfVectorizer(max_features=8192)
  matrix = vectorizer.fit_transform(texts)
  q_vec = vectorizer.transform([query])
  sims = cosine_similarity(q_vec, matrix)[0]
  top_idx = sims.argsort()[::-1][:top_k]
  return [docs[i] for i in top_idx if sims[i] > 0]

