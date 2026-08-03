"""
tests/test_core.py — Unit tests for SecondSelf core modules.
"""

import unittest
import numpy as np
import os
from pathlib import Path

import config
from lib import embeddings, storage
import build_graph
import ask


class TestConfig(unittest.TestCase):
    def test_paths_exist(self):
        self.assertIsInstance(config.PROJECT_ROOT, Path)
        self.assertIsInstance(config.WIKI_DIR, Path)
        self.assertIsInstance(config.DATA_DIR, Path)
        self.assertIsInstance(config.GRAPH_PATH, Path)

    def test_groq_configured(self):
        # Result should be a boolean
        self.assertIsInstance(config.groq_configured(), bool)


class TestEmbeddings(unittest.TestCase):
    def test_cosine_similarity_identical(self):
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        sim = embeddings.cosine_similarity(v1, v2)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_cosine_similarity_orthogonal(self):
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        sim = embeddings.cosine_similarity(v1, v2)
        self.assertAlmostEqual(sim, 0.0, places=5)


class TestBuildGraphHelpers(unittest.TestCase):
    def test_snippet_extraction(self):
        body = "This is a `code` test with [[wikilink]] and [link](http://example.com)."
        snippet = build_graph._snippet(body)
        self.assertEqual(snippet, "This is a test with wikilink and link.")

    def test_normalize(self):
        norm = build_graph._normalize("Hello World 123")
        self.assertEqual(norm, "hello-world-123")

    def test_wikilink_regex(self):
        matches = build_graph.WIKILINK_RE.findall("Check out [[note-1]] and [[note-2]]")
        self.assertEqual(matches, ["note-1", "note-2"])


class TestAskHelpers(unittest.TestCase):
    def test_normalize_query(self):
        norm = ask._normalize_query("What is SecondSelf?")
        self.assertEqual(norm, "what is secondself")

    def test_extract_urls_and_emails(self):
        text = "Contact me at user@example.com or visit https://example.com"
        extracted = ask._extract_urls_and_emails(text)
        self.assertIn("user@example.com", extracted)
        self.assertIn("https://example.com", extracted)


class TestStorage(unittest.TestCase):
    def test_read_wiki_notes(self):
        notes = storage.read_wiki_notes()
        self.assertIsInstance(notes, list)
        if notes:
            first = notes[0]
            self.assertTrue(hasattr(first, "id"))
            self.assertTrue(hasattr(first, "para"))


if __name__ == "__main__":
    unittest.main()
