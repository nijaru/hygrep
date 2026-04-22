# omengrep Handoff Document

**Date:** 2026-04-05
**Project Phase:** `v0.0.3-rc.1` -> `v0.0.4` Development

## 1. What we accomplished this session

### Build Throughput & Memory Scaling
- **Streaming Pipeline (`mpsc`):** Completely refactored `og build` so that `tree-sitter` extraction happens in parallel `rayon` threads, but the results stream directly into the embedding/store thread via a bounded `mpsc::sync_channel`. This eliminates the massive intermediate memory spike that occurred when collecting the entire repository's blocks into a single vector.
- **omendb Update:** Bumped `omendb` dependency to `0.0.36`, picking up its native `mmap` feature which further flattens our memory footprint for massive local repositories.

## 2. Research: Evolving from "Semantic Grep" to "Code Intelligence Engine"

Based on our market research into the 2026 AI coding landscape (Cursor, Windsurf, Claude Code), we explored a potential product direction (NO DECISION MADE YET):

- **The Problem:** Modern agents don't need massive "repo maps" (Aider's approach is outdated). They suffer from context window bloat and need **surgical context injection**.
- **The Exploration:** Should `omengrep` explicitly lean into a role as an **Agentic Code Intelligence Engine**? We already have multi-vector embeddings, structural parsing (via `tree-sitter`), and a built-in MCP server.
- **UX Considerations for Skeletons:** If we go this route, the upcoming Code Skeletons feature (`og outline --skeleton`) might need to **strip docstrings and function bodies by default** to save tokens. Agents only need raw structural signatures to build their internal model of a file. We are keeping this as an open question for further research.

*(This exploration is documented in `ai/DECISIONS.md` and logged to task `tk-cxwy`).*

## 3. Immediate Next Steps

1. **Continue Research / Implement Code Skeletons (`tk-cxwy`):**
   - Head to `src/extractor/mod.rs` and the language-specific query files.
   - Experiment with extraction logic that yields purely the signature/declaration of functions, classes, and structs. 
   - Decide how to handle docstrings (strip by default, include by default, or make configurable) based on further agent testing.

2. **Mini-Golden Benchmark (`tk-g6rq`):**
   - Create a static 20-file corpus in `bench/golden` with 5 hand-crafted semantic queries.
   - We need this for instant (<1s) feedback on extraction/retrieval quality changes now that the 156k-document CoIR benchmark has been suspended for being too heavy for fast iteration.