# Changelog

## [Unreleased]

### Added

- `og context <file|dir>` — show ranked file and symbol context from the existing index. Supports `--json`, `--skeleton`, `-n`, `--symbols`, and the `repomap` alias.
- Migration to Rust Edition 2024.
- High-performance zero-copy indexing using `into_par_iter` to reduce string allocations.
- Optimized Tree-sitter extraction with direct UTF-8 text access.
- Improved fallback indexing for large/unparseable files using byte-indexed line limits.
- **Performance:** Parallelized `ignore::WalkBuilder` during file scanning.
- **Performance:** Parallelized hybrid search (BM25 and MaxSim run concurrently via `rayon::join`) on multi-core CPUs.
- **UX:** Integrated `indicatif` spinner for clean, glitch-free progress reporting during `og build`.

### Changed

- Updated `omendb` to `0.0.36` (registry).
- Benchmarks modernized to match latest `omendb` API and traits.

## [0.0.2] - 2026-03-04

### Added

- `og outline <file|dir>` — show block structure (name, type, line) for indexed files without content. Reads manifest metadata directly, no embedder load. Supports `--json` output.
- `--context/-C N` — configurable content preview lines (default 5). No width truncation; terminal wraps naturally.
- `--regex/-e PATTERN` — post-search filter applied to content and block name.
- BM25 synonym expansion (`src/synonyms.rs`) — ~120-entry vocabulary table expands query terms at search time (e.g., `auth` → `authenticate login session token`). No model or index rebuild required.

### Changed

- `--no-content` replaces `--compact/-c`.
- `--threshold` is now the primary flag; `--min-score` alias removed (v0.0.x, no compatibility obligation).
- `doc_max_length` bumped from 512 to 1024 tokens — large functions no longer truncated. Model supports up to 2048.

### Fixed

- Scope filter sibling directory leak (`starts_with` → exact match + slash guard).
- Markdown chunk IDs — only the last chunk survived before; `chunk_idx` now part of block ID.
- Score display — showed "N% similar" instead of raw score.
- Double ONNX model load on `og clean` and `og status`.
- Dead code branches in status/clean model version check.

## [0.0.1] - 2026-02-23

Initial release.

- Semantic code search with multi-vector embeddings + BM25 hybrid
- Tree-sitter extraction (25 languages)
- LateOn-Code-edge INT8 model (17M params, 48d/token)
- omendb multi-vector store with MuVERA MaxSim reranking
- File references: `file#name`, `file:line`
- Index hierarchy: build checks parent, merges subdirs
- Auto-update: mtime pre-check before each search
- MCP server (`og mcp`) with `og_search`, `og_similar`, `og_status` tools
- Code-aware ranking boosts
