# Architectural Decisions

## 1. Language & Runtime

**Decision:** Mojo + ONNX Runtime
**Why:**

- **Mojo:** Native performance for systems code (Scanner).
- **ONNX Runtime:** Industry standard for inference. Using Python Interop for now (stability).

## 2. Core Architecture: "Hyper Hybrid" (Stateless)

**Decision:** Two-Stage Pipeline: Recall (Regex) -> Rerank (Semantic).
**Rationale:**

- **Statelessness:** No background daemons, no index maintenance. This is our key differentiator against `mgrep` and `morph`.
- **Recall:** Fast "dumb" regex scanning (Mojo) finds candidates (~100 files).
- **Rerank:** "Smart" Cross-Encoder (`mxbai`) scores them.

## 3. Context Strategy (Smart Context)

**Decision:** Tiered Extraction Strategy (Tree-sitter -> Fallback).
**Why:** Agents need logical blocks (functions), not just lines.

- **Tier 1 (Code):** Use Tree-sitter (in Python stage) to extract full functions/classes for candidates.
- **Tier 2 (Docs):** Sliding window (+/- 5 lines) for unsupported files.

## 4. Optimization Strategy

**Decision:** Parallelize IO, Native Regex
**Why:** Python overhead is acceptable for the _Reranker_ (run on <100 items), but unacceptable for the _Scanner_ (run on 50,000 items).

- **Scanner:** Pure Mojo/C (Parallel).
- **Reranker:** Python Interop (Vectorized) + Tree-sitter.

## 5. Parallel Implementation

**Decision:** `algorithm.parallelize` with `UnsafePointer` Mask.
**Why:**

- Mojo's `List` is not thread-safe for concurrent writes.
- Allocating a boolean mask (thread-safe writing by index) prevents locks/contention.

## 6. Distribution Strategy (2025-12-01, Updated)

**Decision:** Mojo as Python Extension Module
**Choice:** Python CLI + Mojo native extension → PyPI wheel

**Discovery:** Mojo supports `PythonModuleBuilder` for building native Python extensions:

```bash
mojo build scanner.mojo --emit shared-lib -o _scanner.so
python -c "from _scanner import scan; scan(...)"  # Native speed!
```

**Architecture:**

```
hygrep (Python CLI) → _scanner.so (Mojo extension) → reranker (Python/ONNX)
```

**Why this works:**

- Native call overhead (~0.01ms vs ~6ms subprocess)
- `pip install hygrep` / `uv tool install hygrep` just works
- Keep Mojo scanner code (no Rust rewrite)
- Python handles deps (onnxruntime, tree-sitter, etc.)

**Implementation:**

1. Refactor `walker.mojo` → `_scanner.mojo` (Python extension API)
2. Python CLI entry point imports `_scanner` directly
3. GitHub Actions builds platform wheels (macOS-arm64, linux-x64)
4. Publish to PyPI as `hygrep`

**Trade-offs:**

- Need Mojo SDK in CI (vs maturin for Rust)
- Manual wheel packaging (no maturin equivalent yet)
- Python startup overhead (~50ms) - acceptable for CLI

**Long-term:** When Mojo ecosystem matures, can go pure Mojo binary.

## 7. Performance Profiling (2025-12-02)

**Findings:**
| Phase | Time | Notes |
|-------|------|-------|
| Scan | ~2ms | Mojo parallel regex - blazing fast |
| Filter | ~0ms | Gitignore + exclude patterns |
| Rerank | ~2200ms | Tree-sitter extraction + ONNX inference |

**Bottleneck:** Rerank phase (98% of total time)

- Model loading: ~500ms first call (cached after)
- Tree-sitter extraction: ~200ms (100 files)
- ONNX inference: ~1500ms (100 candidates @ batch=32)

**Optimizations Applied:**

1. **Query caching** - Pre-compile tree-sitter queries per language (15% improvement)
2. **Parallel extraction** - ThreadPoolExecutor for tree-sitter parsing
3. **Batched inference** - BATCH_SIZE=32, ORT_ENABLE_ALL optimization
4. **max_candidates cap** - Default 100, prevents unbounded inference cost

**Future Options (not implemented):**

- GPU acceleration (onnxruntime-gpu) - 5-10x faster inference
- Daemon mode with warm model - eliminate load time
- Smaller model - quality tradeoff

## 8. GPU Acceleration (2025-12-02, Updated 2025-12-03)

**Decision:** CPU-only until GPU support is ready.

| Provider   | Package                | Status                                 |
| ---------- | ---------------------- | -------------------------------------- |
| CPU        | `onnxruntime`          | ✅ Current                             |
| CUDA       | `onnxruntime-gpu`      | ❌ Not ready                           |
| CoreML     | `onnxruntime-silicon`  | ❌ Not ready (also has spam issues)    |
| DirectML   | `onnxruntime-directml` | ❌ Not ready                           |
| MAX Engine | -                      | ❌ Doesn't support BERT cross-encoders |

CPU is fast enough for now (~2s/100 candidates). Will add GPU when support is ready.

## 9. v2: Semantic-First Architecture (2025-12-04)

**Decision:** Reimagine hhg as semantic code search, dropping stateless grep+rerank.

**Context:**

- v1 was grep → rerank (stateless, instant)
- Users want "find code that does X" not "find code containing X"
- Semantic search requires embeddings → requires index
- Hybrid search research shows semantic + lexical > either alone

**Choice:** Semantic-first with escape hatches

```
hhg "query" path        # Semantic search (default, requires index)
hhg -e "pattern" path   # Exact match (escape hatch, no index)
hhg -r "pattern" path   # Regex match (escape hatch, no index)
```

**Key changes:**

1. Auto-index on first query (no explicit `index build`)
2. Auto-update when stale (incremental)
3. Drop cross-encoder reranking (embeddings sufficient)
4. Drop --fast, --semantic, --hybrid flags (one mode)

**Trade-offs:**
| Aspect | v1 (stateless) | v2 (indexed) |
|--------|----------------|--------------|
| First use | Instant | ~60s index build |
| Subsequent | ~2s | <500ms |
| Maintenance | None | Auto-update |
| Understanding | Lexical only | Semantic |

**Why now:**

- omendb provides fast vector storage
- all-MiniLM-L6-v2 is small (80MB) and fast
- Tree-sitter extraction already exists
- User feedback: semantic understanding > speed

**Rationale:**

> If you want grep, use `rg`. If you want semantic understanding, use `hhg`.

See `ai/DESIGN-v2.md` for full design.

## 10. Code-Aware Ranking Boosts (2025-12-18)

**Decision:** Add post-search heuristic boosts for code-specific ranking.

**Context:**

- Semantic + BM25 hybrid search is good but not code-aware
- Users often search for exact names ("UserManager", "handleAuth")
- Type context matters ("UserManager class" vs just "UserManager")

**Implementation:**

- CamelCase/snake_case splitting for term matching
- Exact name match: 2.5x boost
- Term overlap: +30% per matching term
- Type-aware: 1.5x if query mentions "class"/"function"
- File path relevance: 1.15x
- Boost cap at 4x to prevent over-boosting weak semantic matches

**Rationale:**

- Zero latency overhead (simple heuristics)
- Handles common keyword-style searches well
- Complements semantic understanding

## 11. Optional Cross-Encoder Reranking (Planned)

**Decision:** Add optional reranking for conceptual queries.

**Model:** `jinaai/jina-reranker-v1-tiny-en` (33MB)

**When it helps:**

- "how does authentication work" (conceptual)
- "error handling patterns" (semantic)
- Queries where bi-encoder embeddings miss nuance

**Implementation plan:**

- Flag: `--rerank` or env: `HHG_RERANK=1`
- Rerank top 20-30 results only
- ~50-80ms overhead (acceptable for CLI)
- Off by default (most queries are keyword-style)

**Quantization:** Not needed - 33MB is already small. INT8 could hurt reranking quality where precision matters more than embedding.

**Status:** Not yet implemented. Code boosts handle most cases well.

## 12. Embedding Model Strategy (2026-01-26)

**Decision:** Stay with snowflake-arctic-embed-s, monitor ColBERT.

**Context:**

- Current model (22M, 384 dims) provides good speed/quality balance
- MLX backend gives 2.57x speedup on Apple Silicon
- New candidates exist but none are compelling upgrades

**Evaluated Options:**

| Model              | Verdict                                      |
| ------------------ | -------------------------------------------- |
| Granite Small R2   | 2x params, 16x context, has code benchmarks  |
| MongoDB LEAF       | Same size, 768 dims, distilled from arctic-m |
| mxbai-edge-colbert | Best quality (+4 pts) but blocked on omendb  |

**Why not switch now:**

1. Current model works well with hybrid search (semantic + BM25)
2. No user complaints about quality
3. ColBERT is the real quality unlock, not single-vector upgrades
4. Switching models requires index rebuild for all users

**When to reconsider:**

- omendb adds multi-vector support → evaluate ColBERT
- User feedback indicates quality issues
- New small model with significant quality gains

**Rationale:** Stability over marginal gains. Wait for infrastructure (omendb ColBERT) before model changes.
