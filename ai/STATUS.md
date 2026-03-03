## Current State

| Metric    | Value                          | Updated    |
| --------- | ------------------------------ | ---------- |
| Package   | omengrep 0.0.1 (binary: og)    | 2026-02-24 |
| Models    | LateOn-Code-edge (48d, single) | 2026-02-16 |
| omendb    | 0.0.30 (multi-vector+compact)  | 2026-02-23 |
| Manifest  | v10 (mtime field)              | 2026-02-23 |
| Toolchain | nightly-2025-12-04             | 2026-02-14 |
| Tests     | 14 integration (26 total)      | 2026-02-23 |

## Architecture

```
Build:  Scan -> Extract (tree-sitter, nested dedup) -> Split identifiers (keyword filter) -> Embed (ort, LateOn-Code-edge) -> Store (omendb multi-vector compact) + index_text (BM25)
Search: scan_metadata (stat only) -> check_and_update (mtime pre-check, read only changed) -> Embed query -> BM25+semantic merge -> Code-aware boost -> Results
MCP:    og mcp (JSON-RPC/stdio) -> og_search, og_similar, og_status tools
```

## Active Work

None.

## Remaining Work

- **Boost investigation** — Recall@1=Recall@5=0 consistently; correct results land at rank ~9. Boost likely hurting NL→code queries. Test with boost disabled to quantify.
- **Full corpus bench** — run with 22091 corpus + 500 queries for production-quality signal (~100 min)
- **MCP** — deferred, CLI sufficient for now

## Benchmarks

Performance bench: `benches/omendb.rs` (divan)

| Benchmark       | Baseline (0.0.30) | Current  | delta |
| --------------- | ----------------- | -------- | ----- |
| search_hybrid   | 392.3 us          | 404.5 us | +3%   |
| search_semantic | 422.0 us          | 539.4 us | +28%  |
| store_write     | 5.25 ms           | 6.169 ms | +18%  |

Quality bench: `bench/quality.py` (CodeSearchNet, 2000 corpus seed=42)

| Run                  | Queries | MRR@10 | R@1  | R@5  | R@10 | Date       |
| -------------------- | ------- | ------ | ---- | ---- | ---- | ---------- |
| baseline             | 100     | 0.0082 | 0.00 | 0.00 | 0.08 | 2026-02-22 |
| after a2a0a02 bundle | 100     | 0.0062 | 0.00 | 0.00 | 0.06 | 2026-02-24 |
| current (confirmed)  | 100     | 0.0062 | 0.00 | 0.00 | 0.06 | 2026-03-03 |
| current (500q)       | 500     | 0.0049 | 0.00 | 0.00 | 0.04 | 2026-03-03 |

**Key finding (2026-03-03):** Recall@1=Recall@5=0 in ALL runs. Correct results always land
at ranks 7-10 (avg ~9). This is a **ranking** failure, not retrieval — BM25+semantic finds
the right code within top-10 but boost reranks it to the bottom. Likely cause: name-match
boost (2.5x) favors blocks with identifier-matching terms over the semantically correct answer
when queries are natural language docstrings.

## Competitive Context

Primary competitor: **ColGrep** (LightOn, Feb 2026). Same model, same architecture.
Uses NextPlaid (PLAID) vs omendb (MuVERA). ColGrep never published MRR/recall numbers.

See `ai/research/benchmark-methodology.md` for full competitive analysis.

## omendb Notes (user is maintainer)

1. **Custom tantivy tokenizer** — for camelCase/snake_case splitting in BM25
2. **Native sparse vector support** — for future SPLADE integration

## Key Files

| File                    | Purpose                             |
| ----------------------- | ----------------------------------- |
| `src/cli/search.rs`     | SearchParams, search + file refs    |
| `src/cli/build.rs`      | Build/update index (shared helper)  |
| `src/index/mod.rs`      | SemanticIndex (omendb multi-vector) |
| `src/index/manifest.rs` | Manifest v10 (mtime field)          |
| `src/index/walker.rs`   | scan + scan_metadata (stat-only)    |
| `src/embedder/onnx.rs`  | ORT inference (query vs doc paths)  |
| `src/tokenize.rs`       | BM25 identifier splitting           |
| `src/boost.rs`          | Code-aware ranking boosts           |
| `src/extractor/mod.rs`  | Extraction + nested block dedup     |
| `benches/omendb.rs`     | Performance benchmark (divan)       |
| `tests/cli.rs`          | Integration tests (assert_cmd)      |
