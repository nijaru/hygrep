# Embedding Model Updates - January 2026

**Date:** 2026-01-26
**Context:** Research for hygrep/hhg CLI code search tool

---

## Summary

Since the last research (2026-01-17), several notable developments:

| Model                  | Params      | Key Update                         | Relevance to hhg                   |
| ---------------------- | ----------- | ---------------------------------- | ---------------------------------- |
| **MongoDB LEAF**       | 23M         | SOTA for <=100M on BEIR            | High - Apache 2.0, ONNX ready      |
| **Granite Small R2**   | 47M         | First small ModernBERT, 8K context | High - Apache 2.0, ONNX ready      |
| **EmbeddingGemma**     | 308M        | Best multilingual under 500M       | Medium - MLX+ONNX, 2K context only |
| **mxbai-edge-colbert** | 17M/32M     | ONNX INT8 now available            | High - if omendb adds ColBERT      |
| **Nomic Embed v2 MoE** | 305M active | First MoE embedder                 | Low - too large for CLI            |

**Recommendation:** Test MongoDB LEAF (mdbr-leaf-ir) as potential replacement for snowflake-arctic-embed-s.

---

## New Models Worth Considering

### 1. MongoDB LEAF (mdbr-leaf-ir) - HIGH PRIORITY

| Attribute      | Value                         |
| -------------- | ----------------------------- |
| Parameters     | 23M                           |
| Dimensions     | 768 (Matryoshka: 768->256)    |
| Context        | 512 tokens                    |
| License        | Apache 2.0                    |
| BEIR Rank      | #1 for <=100M params          |
| Distilled From | snowflake-arctic-embed-m-v1.5 |

**Why it matters:**

- Distillation of larger model into 23M params
- Same quality as arctic-embed-m in smaller package
- MRL support for dimension reduction
- INT8 + binary quantization friendly
- ONNX available

**Limitations:**

- 512 token context (vs 8K for arctic-embed)
- Not code-specific

**Source:** [MongoDB LEAF on HuggingFace](https://huggingface.co/MongoDB/mdbr-leaf-ir)

---

### 2. IBM Granite Embedding Small R2 - HIGH PRIORITY

| Attribute      | Value               |
| -------------- | ------------------- |
| Parameters     | 47M                 |
| Dimensions     | 384                 |
| Context        | 8192 tokens         |
| License        | Apache 2.0          |
| Architecture   | ModernBERT-style    |
| Encoding Speed | 199 docs/sec (H100) |

**Why it matters:**

- First small ModernBERT architecture (12 layers)
- 8K context without quality loss
- Code retrieval benchmarks included (CoIR: 53.8)
- ONNX available via onnx-community
- Apache 2.0 licensed

**Benchmarks:**
| Task | Score |
|------|-------|
| BEIR | 50.9 |
| MTEB-v2 | 61.1 |
| CoIR (code) | 53.8 |
| MLDR | 39.8 |

**Source:** [granite-embedding-small-english-r2 on HuggingFace](https://huggingface.co/ibm-granite/granite-embedding-small-english-r2)

---

### 3. Google EmbeddingGemma - MEDIUM PRIORITY

| Attribute  | Value                               |
| ---------- | ----------------------------------- |
| Parameters | 308M (100M model + 200M embeddings) |
| Dimensions | 768 (Matryoshka: 128-768)           |
| Context    | 2048 tokens                         |
| License    | Gemma License                       |
| MTEB Rank  | #1 multilingual under 500M          |
| Languages  | 100+                                |

**Why it matters:**

- MLX native support
- ONNX available (q4, q8, fp32)
- Sub-15ms latency on EdgeTPU
- Runs in <200MB RAM with quantization

**Limitations:**

- 2K context limit (shorter than 8K standard)
- Not code-specific
- Gemma license (less permissive than Apache 2.0)
- 308M total params (larger than alternatives)

**Source:** [EmbeddingGemma on Google Developers Blog](https://developers.googleblog.com/introducing-embeddinggemma/)

---

## ColBERT Model Updates

### mxbai-edge-colbert ONNX Now Available

| Model                     | ONNX Status    | Size  |
| ------------------------- | -------------- | ----- |
| mxbai-edge-colbert-v0-17m | INT8 available | ~17MB |
| mxbai-edge-colbert-v0-32m | Not yet        | ~32MB |

**Source:** [ryandono/mxbai-edge-colbert-v0-17m-onnx-int8](https://huggingface.co/ryandono/mxbai-edge-colbert-v0-17m-onnx-int8)

**Blocker:** omendb does not support multi-vector/ColBERT storage yet. Would need to track:

- pgvector has an [open issue](https://github.com/pgvector/pgvector/issues/694) for ColBERT
- Qdrant and LanceDB have native ColBERT support
- colbert-live allows ColBERT on any vector DB

---

## MLX Updates

### M5 Neural Accelerator Support

MLX 0.30+ with macOS 26.2+ enables Neural Accelerator on M5 chips:

- 4x speedup for time-to-first-token
- 3.8x faster FLUX image generation

**Impact:** Not immediate (requires M5 hardware), but MLX investment continues to pay off.

### Qwen3 Embeddings for MLX

New project: [qwen3-embeddings-mlx](https://github.com/jakedahn/qwen3-embeddings-mlx)

- 0.6B/4B/8B models
- 44K tokens/sec throughput
- REST API included

**Impact:** Too large for hhg CLI use, but demonstrates MLX embedding ecosystem growth.

---

## omendb Status

| Version     | Current  | Notes |
| ----------- | -------- | ----- |
| Latest      | 0.0.24   |       |
| hygrep uses | >=0.0.23 |       |

**ColBERT/Multi-Vector:** Not supported. No public roadmap found.

**Alternatives if needed:**

- LanceDB - embedded, ColBERT native
- Qdrant - ColBERT via fastembed
- colbert-live - adapter for any vector DB

---

## Comparison: Current vs Candidates

### For hhg (Code Search CLI)

| Model                                  | Params | Dims | Context | Code Quality | Speed  | ONNX | License    |
| -------------------------------------- | ------ | ---- | ------- | ------------ | ------ | ---- | ---------- |
| **snowflake-arctic-embed-s** (current) | 22M    | 384  | 512     | General      | Fast   | Yes  | Apache 2.0 |
| MongoDB LEAF (mdbr-leaf-ir)            | 23M    | 768  | 512     | General      | Fast   | Yes  | Apache 2.0 |
| Granite Small R2                       | 47M    | 384  | 8192    | CoIR: 53.8   | Fast   | Yes  | Apache 2.0 |
| EmbeddingGemma                         | 308M   | 768  | 2048    | General      | Medium | Yes  | Gemma      |

### Recommendation Priority

1. **Test Granite Small R2** - Same 384 dims as arctic-s, 2x params but 16x context, code benchmarks
2. **Test MongoDB LEAF** - Distilled quality, same size as arctic-s, 768 dims
3. **Monitor ColBERT** - mxbai-edge-colbert ONNX ready, waiting on omendb

---

## Snowflake Arctic Updates

### Arctic Embed 2.0 (December 2024)

Last major release was v2.0 with:

- Multilingual support
- Matryoshka (128-byte vectors)
- Up to 8K context via RoPE
- 100+ docs/sec on A10

No updates found since December 2024.

**Source:** [snowflake-arctic-embed-l-v2.0 on HuggingFace](https://huggingface.co/Snowflake/snowflake-arctic-embed-l-v2.0)

---

## Action Items

1. [ ] Benchmark Granite Small R2 vs snowflake-arctic-embed-s
   - Same 384 dims, 2x params, 16x context
   - Has code-specific benchmarks (CoIR)

2. [ ] Benchmark MongoDB LEAF vs snowflake-arctic-embed-s
   - Same ~23M params
   - 768 dims vs 384 (more storage but potentially better quality)

3. [ ] Track omendb for ColBERT support
   - mxbai-edge-colbert-v0-17m ONNX INT8 ready
   - Would enable 55.0 ViDoRe score at 17M params

4. [ ] Consider EmbeddingGemma for multilingual use cases only
   - Not priority for code search
   - MLX support is good though

---

## Sources

- [MongoDB LEAF Blog](https://www.mongodb.com/company/blog/engineering/leaf-distillation-state-of-the-art-text-embedding-models)
- [Granite Embedding R2 Paper](https://arxiv.org/html/2508.21085v1)
- [EmbeddingGemma Blog](https://developers.googleblog.com/introducing-embeddinggemma/)
- [mxbai-edge-colbert Tech Report](https://arxiv.org/abs/2510.14880)
- [MLX M5 Support](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)
- [Nomic Embed v2 Blog](https://www.nomic.ai/blog/posts/nomic-embed-text-v2)

---

_Research date: 2026-01-26_
