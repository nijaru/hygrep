## Current State

| Metric    | Value                          | Updated    |
| --------- | ------------------------------ | ---------- |
| Package   | omengrep 0.0.1 (binary: og)    | 2026-02-16 |
| Models    | LateOn-Code-edge (48d, single) | 2026-02-16 |
| omendb    | 0.0.29 (multi-vector+compact)  | 2026-02-22 |
| Toolchain | nightly-2025-12-04             | 2026-02-14 |
| Tests     | 14 integration (26 total)      | 2026-02-22 |

## Architecture

```
Build:  Scan -> Extract (tree-sitter) -> Split identifiers -> Embed (ort, LateOn-Code-edge) -> Store (omendb multi-vector compact) + index_text (BM25)
Search: Embed query (query tokenizer, 256 max) -> BM25 candidates + semantic candidates -> Merge by ID -> Code-aware boost -> Results
MCP:    og mcp (JSON-RPC/stdio) -> og_search, og_similar, og_status tools
```

## Active Work

### Quality Benchmark (tk-pbf0)

Script: `bench/quality.py` (to be created)

- Corpus: CodeSearchNet Python test split (~14k functions)
- Queries: docstrings as NL queries, 500 sampled
- Metrics: MRR@10, Recall@1/5/10
- Match: gold by file basename `corpus/{idx:06d}.py`
- **Blocker**: HF `code_search_net` dataset broken (loading scripts deprecated)
  - Researcher agent running to find working mirror
  - Try: CoIR-Retrieval org, direct jsonl download from S3/GH
- og JSON output fields: `file`, `name`, `type`, `line`, `score`, `content`
- See `ai/research/benchmark-methodology.md` for full design

### Publish to crates.io (tk-4f2n)

- Blocked on omendb crates.io publish (user is omendb maintainer)
- omendb 0.0.29 API change fixed: `multi_vector_with()` now returns `Result`
  — added `?` at `src/index/mod.rs:581`
- Release pipeline ready: `.github/workflows/release.yml`
- Homebrew formula ready: `nijaru/homebrew-tap/Formula/og.rb`
- Tag `v0.1.0` when unblocked

## Benchmarks

Performance bench added: `benches/omendb.rs` (divan)

| Benchmark       | 0.0.28 median | 0.0.29 median | delta    |
| --------------- | ------------- | ------------- | -------- |
| search_hybrid   | 395.8 µs      | 392.3 µs      | -1%      |
| search_semantic | 454.8 µs      | 422.0 µs      | **-7%**  |
| store_write     | 5.49 ms       | 10.68 ms      | **+94%** |

Write regression filed at `~/github/omendb/cloud/ai/research/omengrep-0029-benchmark.md`.
Root cause: `wal_len()` I/O per write in 0.0.29 auto-checkpoint check. Fix: cache counter in memory.

## Remaining Work

- **Quality benchmark** (tk-pbf0) — resolve dataset source, implement bench/quality.py
- **Rebuild indexes** — after query tokenizer fix, existing indexes have stale embeddings
- **MCP testing** — deferred, CLI is sufficient for now

## Competitive Context

Primary competitor: **ColGrep** (LightOn, Feb 2026). Same model (LateOn-Code-edge), same architecture.
Uses NextPlaid (PLAID) vs omendb (MuVERA). ColGrep never published MRR/recall numbers — gap we can fill.

See `ai/research/benchmark-methodology.md` for full competitive analysis.

## omendb Notes (user is maintainer)

1. **Write regression** in 0.0.29 — `wal_len()` doing I/O per `set()` call (+94% slower)
2. **Custom tantivy tokenizer** — for camelCase/snake_case splitting in BM25
3. **Native sparse vector support** — for future SPLADE integration

## Key Files

| File                   | Purpose                             |
| ---------------------- | ----------------------------------- |
| `src/cli/search.rs`    | SearchParams, search + file refs    |
| `src/cli/build.rs`     | Build/update index (shared helper)  |
| `src/index/mod.rs`     | SemanticIndex (omendb multi-vector) |
| `src/embedder/onnx.rs` | ORT inference (query vs doc paths)  |
| `src/tokenize.rs`      | BM25 identifier splitting           |
| `src/boost.rs`         | Code-aware ranking boosts           |
| `benches/omendb.rs`    | Performance benchmark (divan)       |
| `tests/cli.rs`         | Integration tests (assert_cmd)      |
