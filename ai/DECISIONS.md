# Decisions

## Principles
- **Semantic First:** Precision over lexical speed (CodeDB is the speed benchmark, not the goal).
- **Tiger Style:** Minimum 2 `assert!` per function; fixed loop/recursion bounds.
- **Agent-Centric:** Context engineering (skeletons, repomaps) is the primary value.
- **Local-First:** 100% offline indexing and search.
- **High-Iteration Logic:** Use small local corpora for development; reserve massive datasets for final release validation.

## Log
- **[2026-04-05] Context:** Large codebases load all block structures in memory sequentially causing latency spikes. Upgrading to omendb 0.0.36 unlocks the mmap feature. → **Decision:** Pipe parallel rayon extraction directly to the embedder via an mpsc sync channel. → **Rationale:** Streamlines latency profile and limits maximum active memory.
- **[2026-04-05] Context:** `omengrep`'s core features (tree-sitter extraction, multi-vector embeddings, MCP server) align perfectly with the context needs of modern AI coding agents (e.g., Cursor, Windsurf, Claude Code). → **Exploration:** We are researching evolving the project positioning from a "semantic grep" CLI into an "Agentic Code Intelligence Context Engine." We are investigating whether features like Code Skeletons (`og outline --skeleton`) should prioritize surgical, token-efficient MCP delivery (e.g., stripping docstrings by default) over human-readability. → **Status:** No decision made yet. We are exploring what maximizes an agent's effectiveness.
- **[2026-04-05] Context:** `omengrep` was treating CoIR snippets as plain text. → **Decision:** Enforce `.py` extensions for corpus files in evaluator. → **Rationale:** Enables `tree-sitter` extraction, which is critical for `og`'s multi-vector performance.
- **[2026-04-02] Context:** OmenDB v0.0.34 performance bottlenecks. → **Decision:** Upstream `mmap` and custom tokenizers to `omendb`. → **Rationale:** Critical for monorepo scale; current heap-based vector loading is a hard RAM ceiling.
- **[2026-04-02] Context:** Concurrent Go/Rust tests causing contention. → **Decision:** Move search/walker to parallel models (`rayon`, `mpsc`). → **Rationale:** Maximize M3 Max utilization during high-noise environments.

---

## Historical Decisions

### 1. Rust Rewrite (2026-02-14)
**Decision:** Full rewrite from Python/Mojo to Rust.
**Rationale:** Python startup (~150ms), GIL-limited parallelism, serialized embed/insert loops. omendb is a Rust crate — Python bindings add overhead.

### 2. Multi-Vector Embeddings via MuVERA (2026-02-14)
**Decision:** ColBERT-style token-level embeddings with MuVERA compression, replacing single-vector CLS pooling.
**Rationale:** Single-vector loses structural patterns. Token-level matching preserves per-token semantics.

### 3. BM25 + MuVERA Hybrid Search (2026-02-14)
**Decision:** Two-stage retrieval: BM25 candidate generation, then MuVERA MaxSim reranking.
**Architecture:** `Query -> BM25 (tantivy) candidates -> MuVERA MaxSim rerank -> Code-aware boost -> Results`

### 4. Code-Aware AST Extraction (2025-12-04)
**Decision:** Tree-sitter AST extraction into semantic blocks, not whole-file indexing.
**Rationale:** Extracting functions, classes, methods gives precise, actionable results.

### 5. Code-Aware Ranking Boosts (2025-12-18)
**Decision:** Post-search heuristic boosts for code-specific ranking (Exact name match: 2.5x, etc).

### 6. BM25 Tokenization Strategy (2026-02-14)
**Decision:** Pre-process text with camelCase/snake_case splitting before indexing in BM25.

### 7. Sparse Vectors / SPLADE (2026-02-14)
**Decision:** Wait for omendb native sparse support, then evaluate.

### 8. Naming: omengrep / og (2026-02-14)
**Decision:** Package name `omengrep`, binary name `og`, index directory `.og/`.

### 9. Merged BM25 + Semantic Candidates (2026-02-16)
**Decision:** Run both `search_multi_with_text()` and `query_with_options()` in parallel, merge by ID keeping higher score.

### 10. MCP Server for Agent Integration (2026-02-16)
**Decision:** Manual JSON-RPC over stdio implementing MCP protocol, no external crate.
