## Current State

| Metric    | Value                         | Updated    |
| --------- | ----------------------------- | ---------- |
| Phase     | 27 (model upgrade + MLX)      | 2026-01-10 |
| Version   | 0.0.28                        | 2026-01-10 |
| Package   | `hhg` (renamed from `hygrep`) | 2025-12-16 |
| Branch    | main                          | 2025-12-16 |
| PyPI      | https://pypi.org/project/hhg/ | 2025-12-16 |
| CLI       | `hhg`                         | 2025-12-16 |
| Languages | 28 + prose (md, txt, rst)     | 2025-12-16 |
| Model     | gte-modernbert-base (NEW)     | 2026-01-10 |
| omendb    | >=0.0.23                      | 2026-01-10 |

## Current Work: Model Upgrade + Hardware Acceleration

Switching from jina-code-v2 to gte-modernbert-base for 44% better code retrieval quality.

### Why Switch?

| Metric                  | jina-code-v2 (old) | gte-modernbert-base (new) |
| ----------------------- | ------------------ | ------------------------- |
| **CoIR (code quality)** | ~55%               | **79.3%** (+44%)          |
| MLX support             | Custom code needed | Works out of the box      |
| License                 | Apache 2.0         | Apache 2.0                |
| Params                  | 161M               | 149M                      |
| Context                 | 8K                 | 8K                        |
| Dims                    | 768                | 768                       |

### Target Architecture

| Platform      | Backend              | Model Format | Expected Speed   |
| ------------- | -------------------- | ------------ | ---------------- |
| Apple Silicon | MLX (mlx-embeddings) | safetensors  | ~1700 texts/sec  |
| Linux + CUDA  | ONNX + TensorRT EP   | FP16         | ~1000+ texts/sec |
| Linux + ROCm  | ONNX + MIGraphX EP   | FP16         | ~800+ texts/sec  |
| CPU fallback  | ONNX + CPU EP        | INT8         | ~220 texts/sec   |

### Research Completed

- [Code embedding model comparison](research/code-embedding-model-comparison-2026.md)
- [BGE vs jina-code](research/bge-vs-jina-code.md) - superseded by gte-modernbert

## Tasks

See `tk ls` for implementation tasks.

## Breaking Change

Model switch requires index rebuild. Will:

- Add model version to manifest
- Detect old indexes and prompt for rebuild
- Document in release notes

## Previous Versions

<details>
<summary>v0.0.28 - Multi-provider support</summary>

- Upgrade omendb to 0.0.23
- Progress bar for large builds (50+ files)
- Partial clean - `hhg clean ./subdir`
- Multi-provider ONNX detection (CUDA/CPU)
</details>

## Architecture

```
Build:  Scan → Extract (parallel) → Embed (batched) → Store in omendb
Search: Embed query → Hybrid search (semantic + BM25) → Results

Backend selection (auto-detect):
  macOS + MLX available? → MLX with gte-modernbert (Metal GPU)
  TensorRTExecutionProvider? → ONNX FP16 (NVIDIA optimized)
  MIGraphXExecutionProvider? → ONNX FP16 (AMD optimized)
  CUDAExecutionProvider? → ONNX FP16 (NVIDIA fallback)
  Otherwise → ONNX INT8 (CPU optimized)
```

## Key Files

| File                         | Purpose                               |
| ---------------------------- | ------------------------------------- |
| `src/hygrep/cli.py`          | CLI, subcommand handling              |
| `src/hygrep/embedder.py`     | ONNX embeddings, provider detection   |
| `src/hygrep/mlx_embedder.py` | MLX embeddings (to be created)        |
| `src/hygrep/semantic.py`     | Index management, parallel extraction |
| `src/hygrep/extractor.py`    | Tree-sitter code extraction           |
| `src/scanner/_scanner.mojo`  | Fast file scanning (Mojo)             |
