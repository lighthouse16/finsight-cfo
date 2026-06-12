"""
Tests for WorkspaceDocumentIndex — keyword retrieval, workspace isolation, persistence.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from app.services.data_room.document_index import (
    WorkspaceDocumentIndex,
    DocumentChunk,
    BM25Scorer,
)


@pytest.fixture
def index():
    """Create a temporary index for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = WorkspaceDocumentIndex(storage_path=Path(tmpdir) / "test_index.json")
        yield idx


class TestAddAndRetrieve:
    """Basic add/retrieve operations."""

    def test_add_document_returns_chunk_count(self, index):
        chunks = ["First chunk of text about revenue", "Second chunk about expenses"]
        count = index.add_document("ws-1", "doc-1", chunks)
        assert count == 2
        assert index.total_chunks == 2

    def test_empty_document_skipped(self, index):
        chunks = ["", "   ", "\n"]
        count = index.add_document("ws-1", "doc-empty", chunks)
        assert count == 0

    def test_keyword_search_finds_relevant_chunk(self, index):
        index.add_document("ws-1", "doc-1", [
            "The company revenue grew by 20 percent this year",
            "Operating expenses increased slightly",
        ])
        results = index.retrieve("ws-1", "revenue growth")
        assert len(results) >= 1
        assert "revenue" in results[0].text.lower()

    def test_retrieve_top_k_returns_correct_count(self, index):
        chunks = [f"Chunk number {i} with financial data" for i in range(10)]
        index.add_document("ws-1", "doc-1", chunks)
        results = index.retrieve("ws-1", "financial", top_k=3)
        assert len(results) <= 3

    def test_no_match_returns_empty(self, index):
        index.add_document("ws-1", "doc-1", ["Nothing about finance here"])
        results = index.retrieve("ws-1", "elephant")
        assert len(results) == 0


class TestWorkspaceIsolation:
    """Documents from different workspaces stay separate."""

    def test_workspace_a_not_returned_for_workspace_b(self, index):
        index.add_document("ws-a", "doc-1", ["Revenue of company A is 100M"])
        index.add_document("ws-b", "doc-1", ["Revenue of company B is 200M"])
        results_a = index.retrieve("ws-a", "revenue")
        results_b = index.retrieve("ws-b", "revenue")
        assert len(results_a) == 1
        assert len(results_b) == 1
        assert "company A" in results_a[0].text
        assert "company B" in results_b[0].text

    def test_remove_workspace_clears_all(self, index):
        index.add_document("ws-1", "doc-1", ["Some text"])
        index.add_document("ws-1", "doc-2", ["More text"])
        index.add_document("ws-2", "doc-1", ["Other workspace text"])
        removed = index.remove_workspace("ws-1")
        assert removed == 2
        assert index.total_chunks == 1
        assert index.retrieve("ws-1", "text") == []

    def test_remove_document_clears_specific(self, index):
        index.add_document("ws-1", "doc-1", ["Chunk A"])
        index.add_document("ws-1", "doc-2", ["Chunk B"])
        removed = index.remove_document("ws-1", "doc-1")
        assert removed == 1
        assert index.total_chunks == 1


class TestPersistence:
    """Verify the index persists to and loads from disk."""

    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "index.json"
            idx1 = WorkspaceDocumentIndex(storage_path=path)
            idx1.add_document("ws-1", "doc-1", ["Persistent chunk data"])
            assert idx1.total_chunks == 1

            # Create new instance pointing at same file
            idx2 = WorkspaceDocumentIndex(storage_path=path)
            assert idx2.total_chunks == 1
            results = idx2.retrieve("ws-1", "persistent")
            assert len(results) == 1

    def test_clear_resets_index(self, index):
        index.add_document("ws-1", "doc-1", ["Some data"])
        index.clear()
        assert index.total_chunks == 0


class TestBM25Scorer:
    """Basic BM25 scoring sanity checks."""

    def test_higher_score_for_relevant_doc(self):
        corpus = [
            ["revenue", "growth", "profit", "margin"],
            ["weather", "temperature", "rain"],
        ]
        scorer = BM25Scorer(corpus)
        query = ["revenue", "profit"]
        score_relevant = scorer.score(query, 0)
        score_irrelevant = scorer.score(query, 1)
        assert score_relevant > score_irrelevant

    def test_empty_query_returns_zero(self):
        corpus = [["some", "words"]]
        scorer = BM25Scorer(corpus)
        assert scorer.score([], 0) == 0.0
