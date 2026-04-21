# Status (2026-04-05)

## Current Phase: v0.0.3-rc.1 (Stable) -> v0.0.4 Development

## Active Focus
- **Code Skeletons:** Implementing `tree-sitter` signature extraction for token-efficient retrieval.
- **Iteration Speed:** Moving away from large HuggingFace datasets to a local "Golden Corpus".

## Recent Wins
- **Build Throughput:** Transitioned from memory-heavy extraction to an `mpsc` streaming pipeline into the embedder thread.
- **Dependencies:** Updated `omendb` to `0.0.36`, enabling native `mmap` capabilities.
- **Security Audit:** Comprehensive exclusion list implemented in `src/index/walker.rs`.

## Blockers
- **Large Dataset Benchmarking:** Suspended to maintain iteration speed.
