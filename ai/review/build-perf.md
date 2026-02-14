# Build Performance Analysis: `hhg build -f`

**Date:** 2026-02-14
**Baseline:** ~69s for ~4900 files, ~28k blocks (estimated)
**Test:** 3.2s for 35 files, 203 blocks (measured)
**Platform:** M3 Max, 128GB, release build (thin LTO, codegen-units=1)

## Pipeline Phases

```
Scan (walker.rs)        sequential file I/O, ignore crate
  |
Extract (extractor/)    par_iter, tree-sitter per file
  |
Flatten + Sort          sequential, clones blocks
  |
Embed (embedder/)       sequential batch loop, ONNX inference
  |                       -> tokenize (batch)
  |                       -> session.run() (Mutex<Session>)
  |                       -> L2 normalize (scalar loops)
  |
Store (omendb)          sequential per-block store() calls
  |                       -> MuVERA FDE encode
  |                       -> HNSW insert
  |                       -> MultiVec token storage
  |
Flush + Manifest        disk I/O
```

## Bottleneck Analysis

### B1: Sequential file scanning (walker.rs:75-144)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/walker.rs:75-144`
**Issue:** `WalkBuilder` is used sequentially (`.build()` not `.build_parallel()`). Each file is read with `std::fs::read()` one at a time. For 4900 files, this is pure sequential I/O.
**Impact:** Low-medium. On SSD/APFS this is likely 0.5-2s. The `ignore` crate's `build_parallel()` exists and would allow concurrent directory walking + file reading.
**Effort:** Low. Replace `.build()` with `.build_parallel()` and collect into a concurrent map.
**Expected improvement:** 0.5-1.5s saved.

### B2: Unnecessary cloning in to_process (index/mod.rs:92)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:92`

```rust
to_process.push((path.clone(), content.clone(), rel_path, file_hash));
```

**Issue:** Every file's content (String) is cloned here. For 4900 files, this copies all source text (potentially 50-200MB) just to move it into the processing pipeline. The original `files` HashMap is borrowed immutably, so these clones exist only because ownership is needed in `to_process`.
**Impact:** Medium. ~50-200MB allocation + copy.
**Fix:** Store references or indices instead. Since `files` lives for the entire `index()` call, use `(&'a Path, &'a str, String, String)` with lifetime tied to `files`.
**Effort:** Low.
**Expected improvement:** 0.2-0.5s saved, significant memory reduction.

### B3: Block cloning in flatten (index/mod.rs:123)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:123`

```rust
flat_blocks.push((block.clone(), file_hash.clone()));
```

**Issue:** Every `Block` (containing full source content as String) is cloned when flattening. For ~28k blocks, this duplicates all extracted code content.
**Impact:** Medium. Same order as B2.
**Fix:** Consume `all_blocks` with `into_iter()` instead of borrowing.
**Effort:** Low.
**Expected improvement:** 0.1-0.3s saved, significant memory reduction.

### B4: Double `embedding_text()` computation (index/mod.rs:133, 138)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:133,138`

```rust
flat_blocks.sort_by_key(|(b, _)| b.embedding_text().len());  // 1st call: computes all
let texts: Vec<String> = flat_blocks.iter().map(|(b, _)| b.embedding_text()).collect();  // 2nd call
```

**Issue:** `embedding_text()` allocates a new String each call (`format!("{} {}\n{}", ...)`). Called twice for every block: once for sort key, once for the text vec. For ~28k blocks, that is ~56k string allocations (many containing full source code).
**Impact:** Medium. Each call allocates type+name+content. The sort also calls it O(n log n) times.
**Fix:** Compute texts once, sort the texts vec (with parallel index for blocks), or cache embedding_text in the Block.
**Effort:** Low.
**Expected improvement:** 0.3-1.0s saved.

### B5: ONNX inference is sequential across batches (index/mod.rs:142-175)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:142-175`
**Issue:** The embedding loop is `for start in (0..total).step_by(batch_size)` -- strictly sequential. Each batch does: tokenize -> ONNX inference -> L2 normalize -> store. With ~444 batches, this is the dominant cost.
**Sub-issue:** The `Mutex<Session>` in `onnx.rs:12` prevents any parallelism across batches even if attempted.
**Impact:** HIGH. This is the main bottleneck. ~85-90% of total time is here.
**Effort:** See sub-items below.

### B5a: ONNX session uses Mutex (embedder/onnx.rs:12,61)

**Location:** `/Users/nick/github/nijaru/hygrep/src/embedder/onnx.rs:12,61`

```rust
session: Mutex<ort::session::Session>,
// ...
let mut session = self.session.lock().map_err(|e| anyhow::anyhow!("{e}"))?;
```

**Issue:** ONNX Runtime's Session is not `Send+Sync` by default, so a Mutex is used. This prevents concurrent inference. However, ORT already uses intra-op parallelism (`with_intra_threads(num_cpus)`), so the model already uses all cores during `session.run()`. Multiple sessions would compete for CPU.
**Impact:** Low for CPU-only. The Mutex is not causing contention since there is only one caller thread. The real cost is that ONNX inference itself takes ~150ms per batch of 64.
**Fix:** Not actionable for CPU. For GPU/CoreML acceleration, would need different approach.
**Effort:** N/A.

### B5b: Scalar L2 normalization (embedder/onnx.rs:81-94)

**Location:** `/Users/nick/github/nijaru/hygrep/src/embedder/onnx.rs:81-94`

```rust
for j in 0..num_tokens {
    for k in 0..TOKEN_DIM {
        tokens[[j, k]] = view[[i, j, k]];
    }
    let norm: f32 = (0..TOKEN_DIM).map(|k| tokens[[j, k]].powi(2)).sum::<f32>().sqrt();
    if norm > 1e-9 {
        for k in 0..TOKEN_DIM { tokens[[j, k]] /= norm; }
    }
}
```

**Issue:** Triple nested loop with scalar indexing into ndarray. TOKEN_DIM=48, so inner loops are 48 iterations. The copy from 3D `view` to 2D `tokens` is element-by-element. For batch_size=64 with ~100 tokens each, that is 64*100*48\*3 = ~920k array accesses per batch.
**Impact:** Low-medium. The ONNX forward pass dominates, but this is wasteful. ndarray slice operations or `as_standard_layout()` would be faster.
**Fix:** Use `view.slice(s![i, 0..num_tokens, ..])` to get a view, then normalize rows with ndarray ops.
**Effort:** Low.
**Expected improvement:** 0.5-2s total across all batches.

### B6: Per-block store() calls (index/mod.rs:155-174)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:155-174`

```rust
for (idx, token_emb) in token_embeddings.embeddings.iter().enumerate() {
    let tokens: Vec<Vec<f32>> = (0..token_emb.nrows())
        .map(|r| token_emb.row(r).to_vec())
        .collect();
    // ...
    store.store(&block.id, tokens, metadata)?;
}
```

**Issue:** Each block is stored individually. Per `store()` call, omendb does: validate tokens, apply pooling, MuVERA FDE encode, HNSW insert (O(log n) with graph traversal), WAL write, MultiVec storage add. For ~28k blocks, that is 28k individual HNSW insertions.
**Sub-issue:** `store_batch` exists in omendb (`pub(crate)`) which does parallel FDE encoding via rayon and batched HNSW insertion. But it is not public API.
**Impact:** HIGH. HNSW insertion with graph updates is the second-largest cost after ONNX inference. Batched insertion amortizes the graph update cost.
**Fix:** Either expose `store_batch` in omendb's public API, or batch the `store()` calls. The per-block overhead includes: Vec<Vec<f32>> allocation, token validation, pooling check, FDE encoding, HNSW graph traversal, WAL entry.
**Effort:** Medium (requires omendb change to expose `store_batch`/`set_multi_batch`).
**Expected improvement:** 10-25% of total time (~7-17s saved).

### B6a: ndarray-to-Vec<Vec<f32>> conversion (index/mod.rs:159-161)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:159-161`

```rust
let tokens: Vec<Vec<f32>> = (0..token_emb.nrows())
    .map(|r| token_emb.row(r).to_vec())
    .collect();
```

**Issue:** For each block, converts ndarray Array2<f32> to Vec<Vec<f32>> by copying each row. With ~100 tokens \* 48 dims = 4800 f32s per block, and 64 blocks per batch, that is 307k f32s copied per batch (1.2MB). Across 444 batches: ~540MB of allocations.
**Fix:** If omendb accepted `&[&[f32]]` slices (which it does internally via `store_multi_internal`), could pass ndarray row views directly without allocation. Or use `as_standard_layout().as_slice()` with stride info.
**Effort:** Medium.
**Expected improvement:** 1-3s saved.

### B7: Metadata JSON construction per block (index/mod.rs:163-170)

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:163-170`

```rust
let metadata = serde_json::json!({
    "file": block.file,
    "type": block.block_type,
    "name": block.name,
    "start_line": block.start_line,
    "end_line": block.end_line,
    "content": block.content,
});
```

**Issue:** Full block content is serialized into JSON metadata for every block. This means the source code is stored twice: once as token embeddings (for search), once as JSON metadata (for display). For ~28k blocks, this is significant String allocation.
**Impact:** Low-medium. JSON construction is fast, but the content duplication inflates storage I/O.
**Fix:** Store content separately or lazily, or don't store content in metadata (read from source files at display time).
**Effort:** Medium (changes search result reconstruction).
**Expected improvement:** 1-2s saved on I/O, plus smaller index size.

### B8: Tokenizer cloning (embedder/tokenizer.rs:42)

**Location:** `/Users/nick/github/nijaru/hygrep/src/embedder/tokenizer.rs:42`

```rust
let mut tokenizer = self.tokenizer.clone();
```

**Issue:** The tokenizer is cloned on every `encode_batch()` call just to set truncation/padding params. With 444 batches, that is 444 tokenizer clones (the HuggingFace Tokenizer struct may be non-trivial).
**Fix:** Configure truncation/padding once in `new()` and reuse. Or use `encode_batch_char_offsets` without reconfiguring.
**Effort:** Low.
**Expected improvement:** 0.1-0.5s.

### B9: Text search not actually used during indexing

**Location:** `/Users/nick/github/nijaru/hygrep/src/index/mod.rs:72,172`

```rust
store.enable_text_search()?;
// ...
store.store(&block.id, tokens, metadata)?;  // not set_with_text()
```

**Issue (correctness):** `enable_text_search()` is called, but `store()` is used instead of `set_with_text()`. This means BM25 text is never indexed. The `search_multi_with_text()` call at search time relies on BM25 candidates, so hybrid search may return empty results or fall back poorly.
**Impact:** Correctness bug, not performance.
**Fix:** omendb has no `store_with_text()` for multi-vector data. `set_with_text()` accepts `Vector` (single), not `Vec<Vec<f32>>`. Need to add a `store_with_text()` method in omendb that combines multi-vector `store()` semantics with BM25 text indexing. Or expose `text_index` for manual indexing.
**Effort:** Medium (requires omendb API addition).

## Summary: Prioritized Recommendations

| #   | Fix                                                                         | Impact      | Effort | Estimated Savings |
| --- | --------------------------------------------------------------------------- | ----------- | ------ | ----------------- |
| 1   | Expose `store_batch`/`set_multi_batch` in omendb, use batched storage       | High        | Medium | 7-17s (10-25%)    |
| 2   | Fix B9: use `set_with_text()` for BM25 indexing                             | Correctness | Low    | N/A (bug fix)     |
| 3   | Eliminate double `embedding_text()` (B4)                                    | Medium      | Low    | 0.3-1.0s          |
| 4   | Remove content clones: use refs in to_process (B2), consume in flatten (B3) | Medium      | Low    | 0.3-0.8s          |
| 5   | Use ndarray slice ops for L2 norm (B5b)                                     | Low-Med     | Low    | 0.5-2.0s          |
| 6   | Avoid ndarray->Vec<Vec<f32>> copy (B6a)                                     | Medium      | Medium | 1-3s              |
| 7   | Configure tokenizer once, stop cloning (B8)                                 | Low         | Low    | 0.1-0.5s          |
| 8   | Parallel file scanning with build_parallel (B1)                             | Low-Med     | Low    | 0.5-1.5s          |
| 9   | Don't store content in metadata JSON (B7)                                   | Low-Med     | Medium | 1-2s              |

**Total estimated improvement:** 10-28s (15-40% reduction from 69s baseline).

**Largest single bottleneck:** ONNX inference (~55-60% of time). This is inherent to CPU inference with a transformer model. The M3 Max is already saturating cores with intra-op parallelism. Options:

- CoreML/ANE acceleration via ORT's CoreML EP (significant speedup possible)
- Reduce model: quantize further or use smaller model
- Pre-filter: skip files/blocks unlikely to be searched

**Second largest:** Per-block omendb storage (~20-25% of time). Batch storage with parallel FDE encoding would cut this significantly.

## Quick Wins (implement first)

1. **Fix B9** (correctness): Change `store.store()` to `store.set_with_text()` with embedding text
2. **Fix B4** (double embedding_text): Compute once, sort by precomputed length
3. **Fix B2+B3** (cloning): Use references for to_process, consume all_blocks
4. **Fix B8** (tokenizer clone): Configure once in constructor
5. **Fix B5b** (L2 norm): Use ndarray slice operations

These 5 fixes require no API changes to omendb and should save 1.5-4.5s.
