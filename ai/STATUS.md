## Current State

| Metric    | Value                          | Updated    |
| --------- | ------------------------------ | ---------- |
| Package   | omengrep 0.0.1 → 0.0.2 (wip)   | 2026-03-04 |
| RC tag    | v0.0.2-rc.1                    | 2026-03-04 |
| Models    | LateOn-Code-edge (48d, single) | 2026-02-16 |
| omendb    | 0.0.30 (multi-vector+compact)  | 2026-02-23 |
| Manifest  | v10 (mtime field)              | 2026-02-23 |
| Toolchain | nightly-2025-12-04             | 2026-02-14 |
| Tests     | 17 integration, 17 unit        | 2026-03-04 |

## Architecture

```
Build:  Scan -> Extract (tree-sitter, nested dedup) -> Split identifiers (keyword filter) -> Embed (ort, LateOn-Code-edge) -> Store (omendb multi-vector compact) + index_text (BM25)
Search: scan_metadata (stat only) -> check_and_update (mtime pre-check, read only changed) -> Embed query -> split_identifiers+expand_query (synonyms) -> BM25+semantic merge -> Code-aware boost -> Results
MCP:    og mcp (JSON-RPC/stdio) -> og_search, og_similar, og_status tools
```

## Active Work

v0.0.2-rc.1 tagged. Pending final release: bump Cargo.toml, CHANGELOG, tag v0.0.2, cargo publish, GH release (tk-jw5v).

Next feature: `og outline <file>` — show block structure without content (tk-fuap).

## Shipped This Session (2026-03-04)

| Change                    | Detail                                                   |
| ------------------------- | -------------------------------------------------------- |
| doc_max_length 512 → 1024 | Large functions no longer truncated; model supports 2048 |
| --no-content flag         | Renamed from --compact/-c (was ambiguous vs ColGrep)     |
| --threshold (no alias)    | Dropped --min-score alias; v0.0.x, no compat needed      |
| --context/-C N            | Configurable preview lines (default 5, no width cap)     |
| --regex/-e pattern        | Post-search filter on content+name                       |
| Synonym expansion         | src/synonyms.rs, ~120 entries, query-time BM25 expansion |
| Scope filter bug          | starts_with → exact+slash guard (sibling dir leak)       |
| Markdown chunk IDs        | chunk_idx in block ID (only last chunk survived before)  |
| Score display             | "score: N.NNN" not "N% similar"                          |
| Double ONNX load          | remove_dir_all instead of SemanticIndex::new().clear()   |
| Dead branches removed     | "different model" check in status/clean                  |
| 3 regression tests added  | scope_filter, markdown_chunks, similar_score             |

All 34 tests pass (17 integration + 17 unit).

## Key Findings

**doc_max_length = 1024** (src/embedder/mod.rs `ModelConfig`). Model supports up to 2048.
omendb stores whatever vectors the embedder produces — no internal token count constraint.

**Boost fix impact:** MRR 0.0062 → 0.0458 (7.4x), R@1=0.04, R@5=0.06, R@10=0.06.
R@10=6% ceiling is BM25 retrieval limit on NL→code task. Model optimized for code-to-code.

**ColBERT prefix investigation:** `[Q]`/`[D]` prefixes tokenize correctly but hurt perf
(R@10 2% vs 6%). Reverted. Do not retry.

**130M model:** +7.5 MTEB points but 8x inference slowdown, incompatible vector dimensions
(full rebuild required per model). Hold until current quality benchmarked post-synonym expansion.

**Call graph tracing:** Dropped — large scope, bad parity rationale. Not worth pursuing.

**PostToolUse hook for incremental index:** Already handled — search auto-updates via mtime.

## Competitive Position

See `ai/research/competitive-analysis-2026-03.md` for full analysis.

**Local tools:** ColGrep (Rust, PLAID, same model), grepai (Go, Ollama), osgrep (TS, daemon).
**mgrep:** cloud — files leave machine. Not a local tool.

**Advantages:** File refs unique, true BM25 hybrid merge, index hierarchy, published recall@k.
**Remaining gaps:** No 130M model option, no `outline` command (osgrep has skeleton mode).

## Roadmap

| Task                    | ID      | Priority | Notes                             |
| ----------------------- | ------- | -------- | --------------------------------- |
| v0.0.2 release          | tk-jw5v | p2       | Bump version, CHANGELOG, publish  |
| og outline command      | tk-fuap | p3       | Block structure view, low effort  |
| Publish benchmarks      | tk-i4b4 | p3       | Deferred post-release             |
| 130M model support      | —       | defer    | Benchmark current quality first   |
| BM25-only mode (--bm25) | —       | defer    | Low priority, niche debugging use |

## Benchmarks

Quality bench: `bench/quality.py` (CodeSearchNet, 2000 corpus seed=42)

| Run                  | MRR@10 | R@1  | R@5  | R@10 | Date       |
| -------------------- | ------ | ---- | ---- | ---- | ---------- |
| baseline             | 0.0082 | 0.00 | 0.00 | 0.08 | 2026-02-22 |
| after a2a0a02 bundle | 0.0062 | 0.00 | 0.00 | 0.06 | 2026-02-24 |
| boost fixed          | 0.0458 | 0.04 | 0.06 | 0.06 | 2026-03-03 |

R@10 ceiling at 6% is BM25 retrieval limit on NL→code task. Synonym expansion may raise this.

## omendb Notes (user is maintainer)

1. **Custom tantivy tokenizer** — camelCase/snake_case splitting in BM25
2. **Native sparse vector support** — for future SPLADE integration
3. **No internal token limit** — omengrep's ModelConfig is the only constraint

## Key Files

| File                    | Purpose                                           |
| ----------------------- | ------------------------------------------------- |
| `src/cli/mod.rs`        | CLI definition (clap), arg dispatch               |
| `src/cli/search.rs`     | SearchParams, search + file refs                  |
| `src/cli/build.rs`      | Build/update index (shared helper)                |
| `src/cli/output.rs`     | Result formatting (default/json/no-content/files) |
| `src/index/mod.rs`      | SemanticIndex (omendb multi-vector)               |
| `src/index/manifest.rs` | Manifest v10 (mtime field)                        |
| `src/embedder/mod.rs`   | ModelConfig (doc_max_length: 1024)                |
| `src/synonyms.rs`       | BM25 query expansion (~120 code vocab entries)    |
| `src/boost.rs`          | Code-aware ranking boosts                         |
| `src/extractor/mod.rs`  | Extraction + nested block dedup                   |
| `src/tokenize.rs`       | BM25 identifier splitting                         |
| `tests/cli.rs`          | Integration tests (assert_cmd)                    |
