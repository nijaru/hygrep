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
**Why:** Python overhead is acceptable for the *Reranker* (run on <100 items), but unacceptable for the *Scanner* (run on 50,000 items).
- **Scanner:** Pure Mojo/C (Parallel).
- **Reranker:** Python Interop (Vectorized) + Tree-sitter.

## 5. Parallel Implementation
**Decision:** `algorithm.parallelize` with `UnsafePointer` Mask.
**Why:**
- Mojo's `List` is not thread-safe for concurrent writes.
- Allocating a boolean mask (thread-safe writing by index) prevents locks/contention.

## 6. Distribution Strategy (2025-12-01)
**Decision:** Bundle Python Environment (Tarball) vs Python Package.
**Choice:** **Tarball Bundle** (Short term) -> **Pure Mojo/C Rewrite** (Long term).
**Reasoning:**
- We cannot easily ship as a Python package because we want Mojo to be the entry point (fast startup).
- If Python starts first, we lose the "instant grep" feel.
- **Short Term:** Ship binary + stripped `.pixi` environment + wrapper script.
- **Long Term:** Rewrite `src/inference/bridge.py` in Mojo using C-FFI for ONNX Runtime and Tree-sitter. This will eliminate `libpython` dependency entirely, resulting in a truly standalone binary.
