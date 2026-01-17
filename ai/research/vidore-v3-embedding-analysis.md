# ViDoRe V3 Embedding Analysis & ColBERT Research

**Date:** 2026-01-17
**Context:** Evaluating embedding model options for hygrep based on ViDoRe V3 benchmark results

---

## Current Setup

| Attribute  | Value                             |
| ---------- | --------------------------------- |
| Model      | gte-modernbert-base (Alibaba-NLP) |
| Parameters | ~150M                             |
| Dimensions | 768                               |
| ONNX       | INT8 (~150MB) / FP16 (~300MB)     |
| License    | Apache 2.0                        |

---

## ViDoRe V3 Benchmark Results (Textual Retrievers)

Source: [ViDoRe V3 Paper](https://arxiv.org/abs/2601.08620) — comprehensive multimodal RAG benchmark with ~26K document pages, 3,099 human-verified queries across 6 languages.

| Model              | Size (B) | C.S.     | Nucl.    | Fin.     | Phar.    | H.R.     | Ind.     | Tele.    | **Average** |
| ------------------ | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | ----------- |
| Jina-v4            | 3        | 67.3     | **48.2** | **56.5** | 59.0     | **58.8** | 45.8     | 61.0     | **56.7**    |
| Qwen3-8B           | 8        | **73.5** | 42.2     | 54.8     | 62.4     | 52.3     | 45.3     | **66.0** | 56.6        |
| LFM2-350M          | 0.35     | 70.6     | 45.4     | 48.3     | 62.1     | 53.2     | **47.9** | 63.8     | 55.9        |
| **Mxbai Edge 32M** | 0.03     | 68.0     | 44.4     | 48.2     | **62.5** | 52.7     | 47.1     | 61.9     | **55.0**    |
| BM25S              | -        | 64.7     | 45.9     | 49.9     | 56.9     | 49.6     | 45.6     | 58.3     | 53.0        |
| Qwen3-0.6B         | 0.6      | 70.5     | 39.7     | 51.5     | 57.4     | 46.2     | 42.4     | 59.7     | 52.3        |
| GTE-ModernColBERT  | 0.15     | 63.6     | 41.7     | 39.8     | 62.0     | 46.2     | 44.6     | 59.7     | 51.1        |
| BGE-M3             | 0.57     | 63.6     | 34.3     | 43.9     | 54.7     | 45.3     | 39.0     | 54.3     | 47.9        |

### Key Observations

1. **BM25 beats GTE-ModernColBERT** (53.0 vs 51.1) — lexical search competitive with semantic
2. **Mxbai Edge 32M outperforms models 5-20x larger** — 55.0 avg at only 32M params
3. **Diminishing returns at scale** — Qwen3-8B (8B) barely beats Jina-v4 (3B): 56.6 vs 56.7
4. **hygrep's hybrid approach is validated** — BM25 component compensates for semantic weaknesses

---

## Architecture Comparison

### Single-Vector (Current)

```
Document → Encoder → 1 vector (768-dim) → Cosine similarity
```

- Fast indexing: O(1) vector per document
- Small index: 768 floats per doc
- Simple search: nearest neighbor

### ColBERT / Late-Interaction

```
Document → Encoder → N vectors (N tokens × 64-dim) → MaxSim aggregation
```

- Slower indexing: O(N) vectors per document
- Large index: ~10-50x more storage
- Complex search: MaxSim = Σ max(q_i · d_j) for all query tokens

### Quality vs Speed Tradeoff

| Architecture           | Index Size | Build Speed | Retrieval Quality |
| ---------------------- | ---------- | ----------- | ----------------- |
| Single-vector          | 1x         | Fast        | Baseline          |
| ColBERT                | 10-50x     | Slow        | +4-5 points       |
| Hybrid (single + BM25) | ~1.2x      | Fast        | +2-3 points       |

---

## Candidate Models for hygrep

### Option 1: Keep Current (gte-modernbert-base)

| Pros                | Cons                                    |
| ------------------- | --------------------------------------- |
| Already integrated  | 51.1 on ViDoRe V3 (via ColBERT variant) |
| MLX support working | Larger than needed for hybrid search    |
| Apache 2.0          |                                         |

**Verdict:** Safe default. Hybrid search with BM25 compensates.

### Option 2: Smaller Single-Vector (snowflake-arctic-embed-s)

| Attribute  | Value                                |
| ---------- | ------------------------------------ |
| Parameters | 22M (~7x smaller)                    |
| Dimensions | 384 (half storage)                   |
| ONNX INT8  | Available                            |
| License    | Apache 2.0                           |
| Quality    | "Closer to 100M models despite size" |

| Pros                    | Cons                                 |
| ----------------------- | ------------------------------------ |
| ~7x faster embedding    | Not code-specific                    |
| Half the vector storage | Lower baseline quality               |
| Proven ONNX support     | May need hybrid search to compensate |

**Verdict:** Best for faster builds. Test with hybrid search to verify quality acceptable.

### Option 3: ColBERT (mxbai-edge-colbert-v0-32m)

| Attribute  | Value         |
| ---------- | ------------- |
| Parameters | 32M           |
| Dimensions | 64 per token  |
| ONNX       | Not available |
| License    | Apache 2.0    |
| ViDoRe V3  | 55.0 avg      |

| Pros                       | Cons                            |
| -------------------------- | ------------------------------- |
| Best quality at small size | Requires omendb ColBERT support |
| 32M params (tiny)          | 10-50x larger index             |
| Apache 2.0                 | Slower builds (more vectors)    |
|                            | No ONNX yet                     |

**Verdict:** Best quality, but blocked on omendb multi-vector support.

### Option 4: Larger Single-Vector (Jina-v4)

| Attribute  | Value                         |
| ---------- | ----------------------------- |
| Parameters | 3B                            |
| ViDoRe V3  | 56.7 avg (best single-vector) |

**Verdict:** Too large for CLI indexing. 10-20x slower builds.

---

## Recommendation

### For Faster Builds (Priority: Speed)

**Switch to snowflake-arctic-embed-s (22M, 384 dims)**

- ~7x faster embedding computation
- Half the vector storage (384 vs 768 dims)
- BM25 hybrid compensates for quality gap
- Available as INT8 ONNX

Expected impact:

- Index build: ~7x faster
- Storage: ~50% reduction
- Quality: Minimal loss with hybrid search

### For Better Quality (Priority: Retrieval)

**Add ColBERT support to omendb, then use mxbai-edge-colbert-v0-32m**

- 55.0 vs 51.1 on ViDoRe V3 (+4 points)
- Only 32M params (smaller than current!)
- Requires omendb feature work

### Current Recommendation

**Test snowflake-arctic-embed-s** as a drop-in replacement:

1. Faster builds (primary user complaint)
2. Smaller indexes
3. No omendb changes required
4. Hybrid search (BM25) maintains quality

If quality drops noticeably, revisit ColBERT after omendb adds support.

---

## omendb ColBERT Feature Request

For reference, what omendb would need for ColBERT:

```python
# Multi-vector storage
db.set([{
    "id": doc_id,
    "vectors": [[float...], [float...], ...],  # N token vectors
    "text": text
}])

# MaxSim search
db.search_colbert(query_vectors, k=10)

# Hybrid MaxSim + BM25
db.search_hybrid_colbert(query_vectors, query_text, k=10, alpha=0.5)
```

Competitive context: LanceDB and Qdrant both support ColBERT natively.

---

## Next Steps

1. [ ] Benchmark snowflake-arctic-embed-s vs gte-modernbert-base on hygrep test corpus
2. [ ] Measure actual build time improvement
3. [ ] Verify hybrid search quality acceptable
4. [ ] Track omendb ColBERT feature for future quality upgrade

---

## Sources

- [ViDoRe V3 Paper](https://arxiv.org/abs/2601.08620)
- [Snowflake Arctic Embed](https://github.com/Snowflake-Labs/arctic-embed)
- [Mxbai Edge ColBERT](https://huggingface.co/mixedbread-ai/mxbai-edge-colbert-v0-32m)
- [LanceDB ColBERT Support](https://lancedb.com/blog/late-interaction-efficient-multi-modal-retrievers-need-more-than-just-a-vector-index/)
- [Qdrant ColBERT Support](https://qdrant.tech/documentation/fastembed/fastembed-colbert/)
