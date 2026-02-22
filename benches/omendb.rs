// Benchmarks for omendb hot paths used by omengrep.
//
// Measures the three operations that dominate omengrep's runtime:
//   - store_with_text: called once per block during index build
//   - search_multi_with_text: hybrid BM25 + MaxSim search
//   - query_with_options: pure semantic search
//
// Run: cargo bench --bench omendb
// Compare two builds: run on each, diff the output.

use std::path::PathBuf;

use divan::{black_box, Bencher};
use omendb::{MultiVectorConfig, SearchOptions, VectorStore};

fn main() {
    divan::main();
}

/// Token dimension matching LateOn-Code-edge INT8 (48d/token).
const TOKEN_DIM: usize = 48;

/// Tokens per block — representative of a ~30-line function.
const TOKENS_PER_BLOCK: usize = 32;

/// Number of blocks in the store for search benchmarks.
const STORE_SIZE: usize = 1000;

fn make_tokens(seed: usize) -> Vec<Vec<f32>> {
    (0..TOKENS_PER_BLOCK)
        .map(|i| {
            let base = ((seed * 31 + i * 7) % 97) as f32 / 97.0;
            let mut v = vec![0.0f32; TOKEN_DIM];
            for (j, val) in v.iter_mut().enumerate() {
                *val = (base + j as f32 * 0.01).sin();
            }
            v
        })
        .collect()
}

fn make_store(dir: &PathBuf) -> VectorStore {
    let path = dir.join("bench").to_string_lossy().into_owned();
    let mut store = VectorStore::multi_vector_with(TOKEN_DIM, MultiVectorConfig::compact())
        .unwrap()
        .persist(&path)
        .unwrap();
    store.enable_text_search().unwrap();

    for i in 0..STORE_SIZE {
        let tokens = make_tokens(i);
        let text = format!("fn benchmark_function_{i} token_{i} impl struct");
        let meta = serde_json::json!({
            "file": format!("src/module_{}.rs", i % 20),
            "type": "function",
            "name": format!("benchmark_function_{i}"),
            "start_line": i * 10,
            "end_line": i * 10 + 9,
        });
        store
            .store_with_text(&format!("block-{i}"), tokens, &text, meta)
            .unwrap();
    }
    store.flush().unwrap();
    store
}

// --- Write path ---

#[divan::bench]
fn store_write(bencher: Bencher) {
    let dir = tempfile::tempdir().unwrap();
    let path = dir
        .path()
        .join("write_bench")
        .to_string_lossy()
        .into_owned();
    let mut store = VectorStore::multi_vector_with(TOKEN_DIM, MultiVectorConfig::compact())
        .unwrap()
        .persist(&path)
        .unwrap();
    store.enable_text_search().unwrap();

    let mut counter = 0usize;
    bencher.bench_local(|| {
        let tokens = make_tokens(black_box(counter));
        let token_refs: Vec<&[f32]> = tokens.iter().map(|v| v.as_slice()).collect();
        let _ = token_refs; // suppress unused — we pass tokens directly
        let text = format!("fn function_{counter}");
        let meta = serde_json::json!({"file": "src/lib.rs", "type": "function"});
        store
            .store_with_text(&format!("block-{counter}"), tokens, &text, meta)
            .unwrap();
        counter += 1;
    });
}

// --- Search paths ---

#[divan::bench]
fn search_hybrid(bencher: Bencher) {
    let dir = tempfile::tempdir().unwrap();
    let store = make_store(&dir.path().to_path_buf());

    let query_tokens = make_tokens(42);
    let token_refs: Vec<&[f32]> = query_tokens.iter().map(|v| v.as_slice()).collect();

    bencher.bench_local(|| {
        let results = store
            .search_multi_with_text(
                black_box("fn benchmark_function impl struct"),
                black_box(&token_refs),
                black_box(10),
                None,
            )
            .unwrap();
        black_box(results);
    });
}

#[divan::bench]
fn search_semantic(bencher: Bencher) {
    let dir = tempfile::tempdir().unwrap();
    let store = make_store(&dir.path().to_path_buf());

    let query_tokens = make_tokens(42);
    let token_refs: Vec<&[f32]> = query_tokens.iter().map(|v| v.as_slice()).collect();

    bencher.bench_local(|| {
        let results = store
            .query_with_options(
                black_box(&token_refs),
                black_box(10),
                &SearchOptions::default(),
            )
            .unwrap();
        black_box(results);
    });
}
