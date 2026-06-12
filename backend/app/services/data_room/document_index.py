"""
Lightweight document index for RAG retrieval.

Provides BM25-like keyword search over document chunks with workspace isolation.
Persists to a local JSON file — no vector DB required for local mode.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

_STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "storage"))
_INDEX_FILE = _STORAGE_DIR / "document_index.json"


@dataclass
class DocumentChunk:
    """A single chunk of text extracted from a document."""

    workspace_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_file: str = ""


@dataclass
class IndexEntry:
    """Serializable index entry stored on disk."""

    workspace_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]
    source_file: str


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


def _tokenise(text: str) -> list[str]:
    """Lower-case tokenisation for BM25 scoring."""
    return [t.lower() for t in _TOKEN_PATTERN.findall(text)]


# ---------------------------------------------------------------------------
# BM25 scorer
# ---------------------------------------------------------------------------


class BM25Scorer:
    """Simple BM25 implementation over a static corpus of tokenised documents."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.n_docs = len(corpus)
        self.avg_dl = sum(len(d) for d in corpus) / max(self.n_docs, 1)

        # IDF per term
        self.idf: dict[str, float] = {}
        if self.n_docs > 0:
            df: Counter[str] = Counter()
            for doc in corpus:
                df.update(set(doc))
            n = self.n_docs
            for term, freq in df.items():
                self.idf[term] = math.log(1 + (n - freq + 0.5) / (freq + 0.5))

    def score(self, query: list[str], doc_idx: int) -> float:
        doc = self.corpus[doc_idx]
        dl = len(doc)
        score = 0.0
        for term in query:
            if term not in self.idf:
                continue
            tf = doc.count(term)
            idf = self.idf[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
            score += idf * (numerator / max(denominator, 1e-10))
        return score


# ---------------------------------------------------------------------------
# WorkspaceDocumentIndex
# ---------------------------------------------------------------------------


class WorkspaceDocumentIndex:
    """Keyword-based document index with workspace isolation.

    Persists entries to a local JSON file.  Thread-safe for read operations;
    writes lock internally via the GIL (sufficient for local-dev scale).
    """

    def __init__(self, storage_path: str | Path | None = None):
        self._path = Path(storage_path) if storage_path else _INDEX_FILE
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[IndexEntry] = []
        self._tokenised: list[list[str]] = []
        self._loaded = False
        self._dirty = False

    # -- public API ----------------------------------------------------------

    def add_document(
        self,
        workspace_id: str,
        document_id: str,
        chunks: list[str],
        metadata: dict[str, Any] | None = None,
        source_file: str = "",
    ) -> int:
        """Add a document's text chunks to the index. Returns number of chunks added."""
        self._lazy_load()
        meta = metadata or {}
        added = 0
        for i, text in enumerate(chunks):
            if not text.strip():
                continue
            entry = IndexEntry(
                workspace_id=workspace_id,
                document_id=document_id,
                chunk_index=i,
                text=text.strip(),
                metadata=meta,
                source_file=source_file,
            )
            self._entries.append(entry)
            self._tokenised.append(_tokenise(text))
            added += 1
        self._dirty = True
        self._save()
        return added

    def remove_document(self, workspace_id: str, document_id: str) -> int:
        """Remove all chunks for a given document. Returns number of chunks removed."""
        self._lazy_load()
        before = len(self._entries)
        keep: list[tuple[IndexEntry, list[str]]] = []
        for e, toks in zip(self._entries, self._tokenised):
            if not (e.workspace_id == workspace_id and e.document_id == document_id):
                keep.append((e, toks))
        removed = before - len(keep)
        if removed:
            self._entries = [e for e, _ in keep]
            self._tokenised = [t for _, t in keep]
            self._dirty = True
            self._save()
        return removed

    def remove_workspace(self, workspace_id: str) -> int:
        """Remove all entries for a workspace. Returns number of chunks removed."""
        self._lazy_load()
        before = len(self._entries)
        keep: list[tuple[IndexEntry, list[str]]] = []
        for e, toks in zip(self._entries, self._tokenised):
            if e.workspace_id != workspace_id:
                keep.append((e, toks))
        removed = before - len(keep)
        if removed:
            self._entries = [e for e, _ in keep]
            self._tokenised = [t for _, t in keep]
            self._dirty = True
            self._save()
        return removed

    def retrieve(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[DocumentChunk]:
        """Keyword-search the index, filtered by workspace_id. Returns top-k chunks."""
        self._lazy_load()

        # Filter to workspace entries
        ws_indices = [i for i, e in enumerate(self._entries) if e.workspace_id == workspace_id]
        if not ws_indices:
            return []

        # Tokenise query
        query_tokens = _tokenise(query)
        if not query_tokens:
            return []

        # Build a sub-corpus for the workspace
        ws_entries = [self._entries[i] for i in ws_indices]
        ws_corpus = [self._tokenised[i] for i in ws_indices]

        # Score
        scorer = BM25Scorer(ws_corpus)
        scored: list[tuple[float, int]] = []
        for local_idx, global_idx in enumerate(ws_indices):
            s = scorer.score(query_tokens, local_idx)
            if s > 0:
                scored.append((s, global_idx))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        results: list[DocumentChunk] = []
        for score, global_idx in top:
            e = self._entries[global_idx]
            results.append(
                DocumentChunk(
                    workspace_id=e.workspace_id,
                    document_id=e.document_id,
                    chunk_index=e.chunk_index,
                    text=e.text,
                    metadata=e.metadata,
                    source_file=e.source_file,
                )
            )
        return results

    @property
    def total_chunks(self) -> int:
        self._lazy_load()
        return len(self._entries)

    @property
    def workspace_count(self) -> int:
        self._lazy_load()
        return len({e.workspace_id for e in self._entries})

    def clear(self) -> None:
        self._entries.clear()
        self._tokenised.clear()
        self._dirty = True
        self._save()

    # -- persistence ---------------------------------------------------------

    def _lazy_load(self) -> None:
        if self._loaded:
            return
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                for item in data:
                    self._entries.append(IndexEntry(**item))
                    self._tokenised.append(_tokenise(item["text"]))
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # start fresh on corrupt data
        self._loaded = True

    def _save(self) -> None:
        if not self._dirty:
            return
        data = [asdict(e) for e in self._entries]
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self._dirty = False


# ---------------------------------------------------------------------------
# Singleton convenience
# ---------------------------------------------------------------------------

_index_instance: WorkspaceDocumentIndex | None = None


def get_document_index() -> WorkspaceDocumentIndex:
    """Return a shared singleton index instance."""
    global _index_instance
    if _index_instance is None:
        _index_instance = WorkspaceDocumentIndex()
    return _index_instance
