# Status (2026-04-23)

## Current Phase: v0.0.3-rc.1 (Stable) -> v0.0.4 Development

## Active Focus
- **Benchmarking:** CoIR Benchmark Harness setup.
- **Agent Context:** Exploring PageRank-based RepoMap generation.

## Recent Wins
- **Code Skeletons:** Implemented `tree-sitter` signature extraction (`og outline --skeleton`), stripping function bodies to optimize token usage for AI agents.
- **Iteration Speed:** Created a local "Golden Corpus" benchmark in `bench/golden` for instant (<1s) evaluation loops (MRR/Recall).
- **Build Throughput:** Transitioned from memory-heavy extraction to an `mpsc` streaming pipeline into the embedder thread.
- **Dependencies:** Updated `omendb` to `0.0.36`, enabling native `mmap` capabilities.
- **Security Audit:** Comprehensive exclusion list implemented in `src/index/walker.rs`.

## Blockers
- None
