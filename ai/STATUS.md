## Current State

| Metric    | Value                      | Updated    |
| --------- | -------------------------- | ---------- |
| Version   | 0.1.0 (Rust)               | 2026-02-14 |
| Model     | LateOn-Code-edge (48d/tok) | 2026-02-14 |
| omendb    | 0.0.27 (multi-vector)      | 2026-02-14 |
| Toolchain | nightly-2025-12-04         | 2026-02-14 |

## Rust Rewrite

**Status:** Phases 1-6 complete. Compiles, CLI works, all commands implemented.

**Architecture:**

```
Build:  Scan (ignore crate) -> Extract (tree-sitter, 25 langs) -> Embed (ort, LateOn-Code-edge INT8) -> Store (omendb multi-vector) + index_text (BM25)
Search: Embed query -> search_multi_with_text (BM25 candidates + MuVERA MaxSim rerank) -> Code-aware boost -> Results
```

## Bugs Fixed This Session

- **BM25 text never indexed:** `store()` for multi-vector doesn't call `index_text()`. `search_multi_with_text()` returned empty silently. Fixed: added `index_text()` to omendb, called after `store()` in hhg. Filed bug report for omendb to add `store_with_text()`.
- **target/ not gitignored:** Rust build artifacts scanned, inflating index from 69 to 1165 files. Fixed.

## Benchmark (vs competitor, hygrep repo)

| Metric | Competitor | hhg | Notes |
|--------|-----------|-----|-------|
| Build | 6.1s (63 files) | 10.8s (69 files, 801 blocks) | hhg indexes 5x more data |
| Search | 1.0-1.1s | 0.27-0.44s | **hhg 2.5-4x faster** |
| Index size | 14MB | 38MB | Multi-vector + BM25 text |

## Remaining Work

### Priority 1: Correctness (tk-zvga)

- Systematic edge case verification post-rewrite
- Search was silently broken until this session — what else is wrong?
- Test: incremental update, file deletion, merge, stale detection, file refs, all output formats, exit codes

### Priority 2: Polish & Parity (tk-we4e)

- Verify CLI flags/output match Python version
- Integration tests with assert_cmd

### Priority 3: Profile build (tk-kwzw), Rename (tk-uwun), Distribution (tk-4f2n, tk-8yhl)

- Build is 1.3x slower while indexing 5x more — already good, profile for low-hanging fruit
- Rename to omgrep (crate) / omg (binary) — ties branding to omendb
- crates.io + npm + cargo-dist

### Future: SPLADE sparse vectors

- Wait for omendb native sparse support
- Evaluate `ibm-granite/granite-embedding-30m-sparse` (30M, Apache 2.0, 50.8 nDCG)
- Near-term: improve BM25 tokenization with camelCase/snake_case splitting in tantivy

## Key Files (Rust)

| File                   | Purpose                             |
| ---------------------- | ----------------------------------- |
| `src/cli/search.rs`    | Search command + file ref parsing   |
| `src/cli/build.rs`     | Build/update index                  |
| `src/embedder/onnx.rs` | ORT inference (LateOn-Code-edge)    |
| `src/extractor/mod.rs` | Tree-sitter extraction coordinator  |
| `src/index/mod.rs`     | SemanticIndex (omendb multi-vector) |
| `src/index/walker.rs`  | File walker (ignore crate)          |
| `src/types.rs`         | Block, SearchResult, FileRef        |

## Research

| File                                   | Topic                              |
| -------------------------------------- | ---------------------------------- |
| `research/multi-vector-code-search.md` | ColBERT/multi-vector model eval    |
| `tmp/splade-research.md`               | SPLADE vs BM25 for code (gitignored) |
| `tmp/twitter-post-draft.md`            | omendb marketing draft (gitignored)  |
