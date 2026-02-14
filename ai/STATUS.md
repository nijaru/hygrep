## Current State

| Metric    | Value                      | Updated    |
| --------- | -------------------------- | ---------- |
| Version   | 0.1.0 (Rust)               | 2026-02-14 |
| Model     | LateOn-Code-edge (48d/tok) | 2026-02-14 |
| omendb    | 0.0.27 (multi-vector)      | 2026-02-14 |
| Toolchain | nightly-2025-12-04         | 2026-02-14 |

## Architecture

```
Build:  Scan (ignore crate) -> Extract (tree-sitter, 25 langs) -> Embed (ort, LateOn-Code-edge INT8) -> Store (omendb multi-vector) + index_text (BM25)
Search: Embed query -> search_multi_with_text (BM25 candidates + MuVERA MaxSim rerank) -> Code-aware boost -> Results
```

## Benchmark (hygrep repo, M3 Max)

| Metric       | Value                          |
| ------------ | ------------------------------ |
| Build        | 10.8s (69 files, 801 blocks)   |
| Search       | 270-440ms                      |
| Index size   | 38MB (multi-vector + BM25)     |
| Throughput   | ~71 blocks/s                   |

## Remaining Work

### Priority 1: Correctness (tk-zvga)

- Systematic edge case verification post-rewrite
- Search was silently broken until BM25 fix — what else is wrong?
- Test: incremental update, file deletion, merge, stale detection, file refs, all output formats, exit codes

### Priority 2: BM25 Code Tokenization (tk-bm25)

- Pre-split camelCase/snake_case before `index_text()` — immediate fix
- Request custom tokenizer config in omendb `TextSearchConfig` — clean solution
- Zero inference cost, directly improves keyword recall

### Priority 3: Polish & Parity (tk-we4e)

- Verify CLI flags/output match Python version
- Integration tests with assert_cmd

### Priority 4: Profile build (tk-kwzw), Rename (tk-uwun), Distribution (tk-4f2n, tk-8yhl)

- Build is 1.3x slower while indexing 5x more — already good, profile for low-hanging fruit
- Rename to omgrep (crate) / omg (binary) — ties branding to omendb
- crates.io + npm + cargo-dist

### Future: SPLADE Sparse Vectors

- Wait for omendb native sparse support
- Evaluate `ibm-granite/granite-embedding-30m-sparse` (30M, Apache 2.0, 50.8 nDCG)
- Near-term: BM25 tokenization improvements (Priority 2) cover the main gap

## omendb Requests

1. **`store_with_text()`** for multi-vector stores — filed in `omendb/cloud/multi-vector-text-indexing-bug.md`
2. **Custom tantivy tokenizer** in `TextSearchConfig` — for camelCase/snake_case splitting
3. **Native sparse vector support** — for future SPLADE integration

## Key Files (Rust)

| File                   | Purpose                             |
| ---------------------- | ----------------------------------- |
| `src/cli/search.rs`    | Search command + file ref parsing   |
| `src/cli/build.rs`     | Build/update index                  |
| `src/embedder/onnx.rs` | ORT inference (LateOn-Code-edge)    |
| `src/extractor/mod.rs` | Tree-sitter extraction coordinator  |
| `src/index/mod.rs`     | SemanticIndex (omendb multi-vector) |
| `src/index/walker.rs`  | File walker (ignore crate)          |
| `src/boost.rs`         | Code-aware ranking boosts           |
| `src/types.rs`         | Block, SearchResult, FileRef        |

## Research

| File                                   | Topic                              |
| -------------------------------------- | ---------------------------------- |
| `research/multi-vector-code-search.md` | ColBERT/multi-vector model eval    |
| `tmp/splade-research.md`               | SPLADE vs BM25 for code (gitignored) |
| `tmp/twitter-post-draft.md`            | omendb marketing draft (gitignored)  |
