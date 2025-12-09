## Current State

| Metric    | Value                             | Updated    |
| --------- | --------------------------------- | ---------- |
| Phase     | 13 (v2 Simplified)                | 2025-12-08 |
| Version   | 0.0.12 (PyPI)                     | 2025-12-05 |
| Branch    | main                              | 2025-12-08 |
| PyPI      | https://pypi.org/project/hygrep/  | 2025-12-05 |
| CLI       | `hhg` (primary), `hygrep` (alias) | 2025-12-05 |
| Languages | 22                                | 2025-12-03 |
| Perf      | ~20k files/sec (Mojo)             | 2025-12-02 |

## Architecture (Simplified)

Removed cross-encoder reranker and grep modes. Now semantic-only:

| Component              | Status | Notes                                    |
| ---------------------- | ------ | ---------------------------------------- |
| embedder.py            | Done   | ModernBERT-embed-base INT8 (256 dims)    |
| semantic.py            | Done   | SemanticIndex with walk-up discovery     |
| cli.py                 | Done   | 4 commands: build, search, status, clean |
| Walk-up index          | Done   | Reuses parent index from subdirs         |
| Relative paths         | Done   | Manifest v3, portable indexes            |
| Search scope filtering | Done   | Filter results to search directory       |
| Auto-update stale      | Done   | Incremental updates (hash-based)         |
| Explicit build         | Done   | Requires `hhg build` before search       |
| Index hierarchy        | Done   | Parent check, subdir merge, walk-up      |

**Removed in v2.1:**

- Cross-encoder reranker (6s latency not worth marginal quality gain)
- Grep modes (-f, -e, -r) - use ripgrep instead
- reranker.py, test_reranker.py

**Commands:**

```
hhg build ./src       # Build index (required first)
hhg "query" ./src     # Semantic search
hhg status ./src      # Show index status
hhg clean ./src       # Delete index
```

**Performance (M3 Max):**

| Phase       | Time   | Notes                             |
| ----------- | ------ | --------------------------------- |
| First index | ~34s   | 396 blocks, ModernBERT 512 tokens |
| Cold search | ~0.9s  | Model loading                     |
| Warm search | <1ms   | omendb vector search              |
| Auto-update | ~100ms | Per changed file                  |

## Blockers

None.

## Known Issues

- Mojo native scanner requires MAX/Mojo runtime (wheels use Python fallback)

## Next Steps

1. Wait for seerdb/omendb releases with hybrid search (BM25 + semantic)
2. Integrate hybrid search API when available
3. Tag new release after dep updates

## Branch Status

| Branch | Purpose            | Status |
| ------ | ------------------ | ------ |
| main   | v2 semantic stable | Active |
