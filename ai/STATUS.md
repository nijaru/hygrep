# Status (2026-04-26)

## Current Phase: v0.0.3-rc.1 (Stable) -> v0.0.4 Development

## Active Focus
- **Agent Context:** PageRank-based RepoMap generation (`tk-8sk7`).
- **Benchmarking:** Full CoIR runs can now use `bench/coir_eval.py`; smoke validation passed.

## Recent Wins
- **CoIR Harness:** Added fresh-index CoSQA evaluator smoke path and fixed bulk-index stalls found during validation.
- **Code Skeletons:** Implemented `tree-sitter` signature extraction (`og outline --skeleton`), stripping function bodies to optimize token usage for AI agents.
- **Iteration Speed:** Created a local "Golden Corpus" benchmark in `bench/golden` for instant (<1s) evaluation loops (MRR/Recall).
- **Build Throughput:** Transitioned from memory-heavy extraction to an `mpsc` streaming pipeline into the embedder thread.
- **Dependencies:** Updated `omendb` to `0.0.36`, enabling native `mmap` capabilities.
- **Security Audit:** Comprehensive exclusion list implemented in `src/index/walker.rs`.

## Blockers
- None
