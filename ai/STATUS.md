## Current State

| Metric  | Value                        | Updated    |
| ------- | ---------------------------- | ---------- |
| Version | 0.0.32                       | 2026-01-17 |
| PyPI    | https://pypi.org/project/hhg | 2026-01-17 |
| Model   | snowflake-arctic-embed-s     | 2026-01-17 |
| omendb  | >=0.0.23                     | 2026-01-10 |

## Architecture

```
Build:  Scan → Extract (parallel) → Embed (batched) → Store in omendb
Search: Embed query → Hybrid search (semantic + BM25) → Results

Backend selection (auto-detected):
  MLX (Metal GPU) - macOS Apple Silicon, 2.57x faster
  ONNX INT8 (CPU) - all other platforms
```

## Next Steps

### Model Evaluation (Low Priority)

Candidates to benchmark when ready:

| Model              | Params | Dims   | Context | Why Consider                    |
| ------------------ | ------ | ------ | ------- | ------------------------------- |
| Granite Small R2   | 47M    | 384    | 8192    | Code benchmarks, 16x context    |
| MongoDB LEAF       | 23M    | 768    | 512     | SOTA for <=100M, same size      |
| mxbai-edge-colbert | 17M    | 64/tok | -       | 55.0 ViDoRe (blocked on omendb) |

Current `snowflake-arctic-embed-s` is working well. No urgency to switch.

### ColBERT Support (Blocked)

omendb does not support multi-vector storage. When it does:

- mxbai-edge-colbert-v0-17m ONNX INT8 is ready
- Would give +4 quality points at smaller model size

Alternatives if needed: LanceDB, Qdrant (both have native ColBERT).

## Key Files

| File                         | Purpose                            |
| ---------------------------- | ---------------------------------- |
| `src/hygrep/_common.py`      | Shared constants and utilities     |
| `src/hygrep/embedder.py`     | ONNX embeddings, protocol, factory |
| `src/hygrep/mlx_embedder.py` | MLX embeddings (Apple Silicon)     |
| `src/hygrep/semantic.py`     | Index management, hybrid search    |

## Research

| File                                               | Topic                |
| -------------------------------------------------- | -------------------- |
| `research/embedding-models-update-2026-01.md`      | Latest model options |
| `research/vidore-v3-embedding-analysis.md`         | ViDoRe V3 benchmarks |
| `research/code-embedding-model-comparison-2026.md` | Code embeddings      |
