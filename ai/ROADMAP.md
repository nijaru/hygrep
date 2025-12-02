# Strategic Roadmap

**Goal:** Build `hygrep` - The high-performance Hybrid Search CLI.

## Phase 1: Prototype (Completed)
**Goal:** functional End-to-End pipeline (Scanner -> Reranker).
- [x] Basic Directory Walker (Sequential, Mojo).
- [x] Regex Matching (Python `re` wrapper).
- [x] Reranker Integration (Python `onnxruntime` wrapper).
- [x] Single-command CLI wiring.

## Phase 2: Optimization (Completed)
**Goal:** Replace Python components in the "Hot Loop" (Scanner) with Native Mojo/C.
- [x] **FFI:** Implemented `src/scanner/c_regex.mojo` (Native `libc` binding).
- [x] **Parallelism:** Implemented `src/scanner/walker.mojo` with `algorithm.parallelize`.
- [x] **Benchmark:** Achieved ~19k files/sec (Scanner).

## Phase 3: Smart Context (Completed)
**Goal:** Upgrade the "Rerank" phase to provide "Agent-Ready" context.
- [x] **Architecture:** Implemented `src/inference/bridge.py` (Python Bridge).
- [x] **Tree-sitter:** Integrated Python bindings for extraction.
- [x] **Extraction:** Implemented `ContextExtractor` for Python, JS, TS, Go, Rust.
- [x] **Output:** Implemented JSON output for Agents.

## Phase 4: Polish & Robustness (Completed)
**Goal:** Professional CLI Experience & Edge Case Handling.
- [x] **Fallback Strategy:** Implemented "Sliding Window" (Match +/- 5 lines) for non-code/large files.
- [x] **Query Expansion:** Implemented heuristic ("login logic" -> "login|logic") to improve Recall.
- [x] **Auto-Setup:** Added automatic model downloading on first run.
- [x] **Distribution:** Created `hygrep.sh` wrapper to handle environment/linking issues.
- [x] **Optimization:** Batched Reranking (32 items) and Mojo Walker string optimization.

## Phase 5: Future (Backlog)
- [ ] **Binary Distribution:** Static linking of `libpython`?
- [ ] **Advanced Query Expansion:** Use local LLM to generate synonyms.
- [ ] **Mmap:** Zero-copy file reading in Scanner.