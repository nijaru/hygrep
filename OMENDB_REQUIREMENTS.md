# OmenDB Requirements for hygrep Hybrid Search

**Purpose**: Document what hygrep needs from omendb to implement hybrid search (BM25 + semantic).

**Current omendb version in hygrep**: `>=0.0.1a1` (pyproject.toml)

---

## Required Features (All Available in v0.0.5+)

Based on omendb v0.0.6, all required features are already implemented:

### 1. Text Indexing on Insert

```python
db.set([{
    "id": "block_123",
    "vector": embedding,
    "text": "def login(user, password): ...",  # Indexes for BM25
    "metadata": {"file": "auth.py", "type": "function", "name": "login"}
}])
```

**Status**: Available - `text` field auto-enables text search on insert.

### 2. Hybrid Search API

```python
results = db.search_hybrid(
    query_vector=query_embedding,
    query_text="authentication login",
    k=10,
    alpha=0.5,      # 0.0=text only, 1.0=vector only
    rrf_k=60,       # RRF fusion constant
)
# Returns: [{"id": "...", "score": 0.85, "metadata": {...}}, ...]
```

**Status**: Available - `search_hybrid()` method exists.

### 3. Text-Only Search (Optional)

```python
results = db.search_text("error handling", k=10)
```

**Status**: Available - `search_text()` method exists.

### 4. Flush for Text Visibility

```python
db.flush()  # Commit text index for immediate search visibility
```

**Status**: Available - `flush()` method exists, auto-called before searches.

---

## Integration Plan for hygrep

### Current State (semantic.py)

```python
# Current: vector-only search with query expansion workaround
results = self.db.search(query_embedding, k=n)

# Current workaround: CODE_SYNONYMS dict for query expansion
# and hybrid_boost() for name matching
```

### Target State

```python
# Target: native hybrid search via omendb
def search(self, query: str, n: int = 10) -> list[dict]:
    query_embedding = self.embedder.embed_one(query)

    results = self.db.search_hybrid(
        query_vector=query_embedding,
        query_text=query,
        k=n,
        alpha=0.5,  # Balance vector + text
    )

    return self._format_results(results)
```

### Migration Steps

1. **Update omendb dependency**: `>=0.0.1a1` → `>=0.0.5`
2. **Add text field during indexing**:
   ```python
   # In build_index():
   db.set([{
       "id": block_id,
       "vector": embedding,
       "text": block["content"],  # NEW: store code for BM25
       "metadata": {
           "file": block["file"],
           "type": block["type"],
           "name": block["name"],
           "start_line": block["start_line"],
           "end_line": block["end_line"],
       }
   }])
   ```
3. **Replace search with hybrid**:
   ```python
   # In search():
   results = db.search_hybrid(query_vector, query, k=n, alpha=0.5)
   ```
4. **Remove workarounds**: Delete `CODE_SYNONYMS`, `expand_query_terms()`, `hybrid_boost()`

---

## API Reference (from omendb v0.0.6)

### set() with text

```python
db.set([{
    "id": str,
    "vector": list[float],
    "text": str,              # Optional: enables hybrid search
    "metadata": dict,         # Optional
}])
```

### search_hybrid()

```python
db.search_hybrid(
    query_vector: list[float] | np.ndarray,
    query_text: str,
    k: int,
    filter: dict = None,      # Optional: metadata filter
    alpha: float = 0.5,       # 0.0=text, 1.0=vector
    rrf_k: int = 60,          # RRF constant
) -> list[dict]
# Returns: [{"id", "score", "metadata"}, ...]
```

### search_text()

```python
db.search_text(
    query: str,
    k: int,
) -> list[dict]
# Returns: [{"id", "score"}, ...]
```

---

## Performance Characteristics

From omendb benchmarks (v0.0.6):

| Operation     | Performance  | Notes               |
| ------------- | ------------ | ------------------- |
| Vector search | ~3,000 QPS   | HNSW + RaBitQ       |
| Text search   | <5ms @ 10K   | Tantivy BM25        |
| Hybrid search | <15ms @ 10K  | Vector + text + RRF |
| Insert w/text | 10K docs/sec | Vector + text index |

---

## Checklist for omendb

- [x] `set()` accepts `text` field
- [x] `search_hybrid()` method exists
- [x] `search_text()` method exists
- [x] `flush()` commits text index
- [x] RRF fusion implemented
- [x] `alpha` parameter for weighting
- [x] `filter` works with hybrid search
- [x] Metadata returned with hybrid results

**Conclusion**: omendb v0.0.5+ has everything hygrep needs. Update dependency and integrate.
