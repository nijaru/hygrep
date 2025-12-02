# Strategic Roadmap

**Goal:** Build `hygrep` - The high-performance Hybrid Search CLI.

## Completed Phases

### Phase 1-4: MVP (Completed)
- [x] Directory walker with parallel scanning (~20k files/sec)
- [x] POSIX regex via libc FFI
- [x] ONNX cross-encoder reranking (mxbai-rerank-xsmall-v1)
- [x] Tree-sitter extraction (Python, JS, TS, Go, Rust)
- [x] JSON output for agents
- [x] Auto model download on first run

### Phase 5: Distribution (Completed)
- [x] Mojo Python extension module (`_scanner.so`)
- [x] Python CLI entry point (`pip install hygrep`)
- [x] Platform-specific wheel tags
- [x] Removed legacy Mojo CLI

## Current: Phase 6 - Performance & Polish (v0.2.0)

**Goal:** 2-3x faster inference, better CLI UX

### Performance (P0)
| Task | Impact | Status |
|------|--------|--------|
| Thread optimization (4 threads) | 2.5x inference speedup | TODO |
| Candidate limit (--max-candidates) | Cap work before rerank | TODO |
| Graph optimization level | Minor speedup | TODO |

**Benchmarks (21 candidates, CPU):**
```
Threads=1: 5537ms
Threads=2: 3490ms (1.6x)
Threads=4: 2260ms (2.5x) ← optimal
Threads=8: 2146ms (diminishing)
```

### CLI Features (P1)
| Task | Use Case | Status |
|------|----------|--------|
| `--fast` mode | Skip reranking, pure grep | TODO |
| `-t/--type` filter | Limit to file types | TODO |
| `--min-score` threshold | Filter low-confidence | TODO |
| Better progress output | Show file count, timing | TODO |

## Phase 7: Features (v0.3.0)

**Goal:** Feature parity with modern search tools

| Feature | Description |
|---------|-------------|
| Gitignore support | Parse .gitignore files |
| Context lines `-C N` | Show surrounding code |
| `--stats` flag | Show timing breakdown |
| Config file `.hygreprc` | Persistent options |
| JSONL streaming | Process results incrementally |

## Phase 8: Hardware Acceleration (v0.4.0+)

**Goal:** Leverage GPU/NPU for inference

### macOS (Apple Silicon)
- CoreML requires custom onnxruntime build
- Alternative: MLX framework
- Expected: 3-5x speedup

### Linux/Windows
- CUDA via `onnxruntime-gpu`
- ROCm for AMD GPUs
- Expected: 5-10x (overhead for small batches)

### Model Options
| Model | Quality | Speed | Size |
|-------|---------|-------|------|
| mxbai-rerank-xsmall-v1 | Good | Fast | 40MB | **Current** |
| mxbai-rerank-base-v2 | Better | 2x slower | 110MB |
| jina-reranker-v1-tiny-en | OK | Fastest | 33MB |

**Decision:** Keep xsmall-v1 default, add `--model` flag later.

## Non-Goals

- Indexing/persistence (stay stateless)
- Background daemon (keep CLI simple)
- Custom model training (use pretrained)
- Server mode (CLI-first design)
