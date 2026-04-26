# Status (2026-04-26)

## Current Phase: v0.0.3-rc.1 (Stable) -> v0.0.4 Development

## Active Focus
- **Roadmap:** Recentered on local code context engine with grep-like UX.
- **Next Build:** Graph-aware context ranking (`tk-8sk7`) as a minimal `og repomap`-style surface.
- **Benchmarking:** CoIR smoke path exists; full runs are available but not the current focus.

## Recent Wins
- **Roadmap Realignment:** Reframed semantic search as the entry point and context surfaces as the product direction.
- **CoIR Harness:** Added fresh-index CoSQA evaluator smoke path and fixed bulk-index stalls found during validation.
- **Code Skeletons:** Implemented `tree-sitter` signature extraction (`og outline --skeleton`), stripping function bodies to optimize token usage for AI agents.
- **Iteration Speed:** Created a local "Golden Corpus" benchmark in `bench/golden` for instant (<1s) evaluation loops (MRR/Recall).
- **Build Throughput:** Transitioned from memory-heavy extraction to an `mpsc` streaming pipeline into the embedder thread.
- **Dependencies:** Updated `omendb` to `0.0.36`, enabling native `mmap` capabilities.
- **Security Audit:** Comprehensive exclusion list implemented in `src/index/walker.rs`.

## Blockers
- None
