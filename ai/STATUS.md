## Current State

| Metric    | Value                         | Updated    |
| --------- | ----------------------------- | ---------- |
| Phase     | 28 (model upgrade complete)   | 2026-01-10 |
| Version   | 0.0.29-dev                    | 2026-01-10 |
| Package   | `hhg` (renamed from `hygrep`) | 2025-12-16 |
| Branch    | main                          | 2025-12-16 |
| PyPI      | https://pypi.org/project/hhg/ | 2025-12-16 |
| CLI       | `hhg`                         | 2025-12-16 |
| Languages | 28 + prose (md, txt, rst)     | 2025-12-16 |
| Model     | gte-modernbert-base           | 2026-01-10 |
| omendb    | >=0.0.23                      | 2026-01-10 |

## Completed: Model Upgrade + Hardware Acceleration

Switched from jina-code-v2 to gte-modernbert-base with MLX support for Apple Silicon.

### Performance

| Platform      | Backend              | Speed (texts/sec) | Notes                 |
| ------------- | -------------------- | ----------------- | --------------------- |
| Apple Silicon | MLX (mlx-embeddings) | 500-2200          | Varies by text length |
| Linux + CUDA  | ONNX + TensorRT EP   | ~1000+            | Auto-detect           |
| Linux + ROCm  | ONNX + MIGraphX EP   | ~800+             | Auto-detect           |
| CPU fallback  | ONNX + CPU EP        | ~330              | INT8 quantized        |

### Implementation Summary

1. **Model**: gte-modernbert-base (79.3% CoIR vs 55% jina-code)
2. **MLX Embedder**: New `mlx_embedder.py` with length-bucketed batching
3. **ONNX Embedder**: Updated for gte-modernbert, TensorRT/MIGraphX EP detection
4. **Manifest**: Version 6 with model tracking, auto-detect old indexes
5. **Dependencies**: `mlx` optional dep for macOS

### Breaking Change

Model switch requires index rebuild:

- Old indexes (v5) prompt: "Rebuild with: hhg build --force"
- Embeddings incompatible between models

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
| `src/hygrep/mlx_embedder.py` | MLX embeddings (Metal GPU)            |
| `src/hygrep/semantic.py`     | Index management, parallel extraction |
| `src/hygrep/extractor.py`    | Tree-sitter code extraction           |
| `src/scanner/_scanner.mojo`  | Fast file scanning (Mojo)             |
