"""Test embedder module."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from hygrep.embedder import DIMENSIONS, Embedder


def test_embedder_init():
    """Test embedder initialization."""
    embedder = Embedder()
    assert embedder._session is None  # Lazy load
    print("Embedder init: PASS")


def test_embed_single():
    """Test embedding a single query."""
    embedder = Embedder()
    embedding = embedder.embed_one("user authentication function")

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (DIMENSIONS,)
    assert embedding.dtype == np.float32

    # Check normalized (L2 norm ~= 1)
    norm = np.linalg.norm(embedding)
    assert 0.99 < norm < 1.01, f"Embedding not normalized: norm={norm}"

    print("Embed single: PASS")


def test_embed_batch():
    """Test embedding a batch of documents."""
    embedder = Embedder()
    texts = [
        "def login(): pass",
        "class User: pass",
        "async def fetch_data(): return []",
    ]

    embeddings = embedder.embed(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, DIMENSIONS)
    assert embeddings.dtype == np.float32

    # Check all normalized
    for i, emb in enumerate(embeddings):
        norm = np.linalg.norm(emb)
        assert 0.99 < norm < 1.01, f"Embedding {i} not normalized: norm={norm}"

    print("Embed batch: PASS")


def test_embed_empty():
    """Test embedding empty list."""
    embedder = Embedder()
    embeddings = embedder.embed([])

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (0, DIMENSIONS)

    print("Embed empty: PASS")


def test_embed_similarity():
    """Test that similar texts have similar embeddings."""
    embedder = Embedder()

    # Similar texts
    text1 = "def authenticate_user(username, password): pass"
    text2 = "def login(user, pwd): pass"
    # Different text
    text3 = "def calculate_sum(a, b): return a + b"

    emb1 = embedder.embed_one(text1)
    emb2 = embedder.embed_one(text2)
    emb3 = embedder.embed_one(text3)

    # Cosine similarity (embeddings are normalized, so dot product = cosine)
    sim_1_2 = np.dot(emb1, emb2)
    sim_1_3 = np.dot(emb1, emb3)

    # Similar auth functions should be more similar than auth vs math
    assert sim_1_2 > sim_1_3, f"Expected sim_1_2 ({sim_1_2:.3f}) > sim_1_3 ({sim_1_3:.3f})"

    print("Embed similarity: PASS")


def test_embed_large_batch():
    """Test embedding a larger batch (tests batching logic)."""
    embedder = Embedder()
    # Create more texts than BATCH_SIZE (16)
    texts = [f"def function_{i}(): return {i}" for i in range(50)]

    embeddings = embedder.embed(texts)

    assert embeddings.shape == (50, DIMENSIONS)

    # Check all normalized
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.all((norms > 0.99) & (norms < 1.01)), "Not all embeddings normalized"

    print("Embed large batch: PASS")


if __name__ == "__main__":
    print("Running embedder tests...\n")
    test_embedder_init()
    test_embed_single()
    test_embed_batch()
    test_embed_empty()
    test_embed_similarity()
    test_embed_large_batch()
    print("\nAll embedder tests passed!")
