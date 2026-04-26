// omengrep - semantic code search
// Benchmarks for omendb integration.
//
// These focus on the hot path of the vector store:
//   - index_multi: inserting multi-vectors
//   - search_multi_with_text: hybrid BM25 + semantic rerank
//   - query_with_options: pure semantic search
//
// Run: cargo bench --bench omendb
// Compare two builds: run on each, diff the output.

use std::path::Path;

use divan::{black_box, Bencher};
use omendb::{MultiVectorConfig, SearchOptions, VectorStore};

fn main() {
    divan::main();
}

const TOKEN_DIM: usize = 48; // LateOn-Code-edge dimension

fn make_tokens(count: usize) -> Vec<Vec<f32>> {
    (0..count)
        .map(|_| {
            let mut v = vec![0.0; TOKEN_DIM];
            for x in &mut v {
                *x = rand::random::<f32>();
            }
            // L2 normalize
            let norm = v.iter().map(|x| x * x).sum::<f32>().sqrt();
            for x in &mut v {
                *x /= norm;
            }
            v
        })
        .collect()
}

fn make_store(dir: &Path) -> VectorStore {
    let path = dir.join("bench").to_string_lossy().into_owned();
    let mut store = VectorStore::multi_vector_with(TOKEN_DIM, MultiVectorConfig::compact())
        .unwrap()
        .persist(&path)
        .unwrap();
    store.enable_text_search().unwrap();

    // Fill with some data (1000 "files", 10 blocks each)
    for i in 0..1000 {
        let content = format!(
            "fn function_{}() {{ let x = {}; println!(\"hello\"); }}",
            i,
            i * 42
        );
        for j in 0..10 {
            let tokens = make_tokens(16); // 16 tokens per block
            let token_refs: Vec<&[f32]> = tokens.iter().map(|v| v.as_slice()).collect();
            let metadata = serde_json::json!({
                "file": format!("file_{}.rs", i),
                "type": "function",
                "name": format!("function_{}", i),
                "start_line": 0,
                "end_line": 2,
                "content": content,
            });
            store
                .store_with_text(&format!("{}_{}", i, j), token_refs, &content, metadata)
                .unwrap();
        }
    }
    store
}

// --- Benchmark insertion path ---

#[divan::bench]
fn index_multi(bencher: Bencher) {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("bench_insert").to_string_lossy().into_owned();
    let mut store = VectorStore::multi_vector_with(TOKEN_DIM, MultiVectorConfig::compact())
        .unwrap()
        .persist(&path)
        .unwrap();
    store.enable_text_search().unwrap();

    let tokens = make_tokens(16);
    let token_refs: Vec<&[f32]> = tokens.iter().map(|v| v.as_slice()).collect();
    let content = "fn test() { println!(\"benchmark\"); }";
    let metadata = serde_json::json!({
        "file": "test.rs",
        "type": "function",
        "name": "test",
        "start_line": 0,
        "end_line": 2,
        "content": content,
    });

    bencher.bench_local(|| {
        store
            .store_with_text(
                black_box("test_id"),
                black_box(token_refs.clone()),
                black_box(content),
                black_box(metadata.clone()),
            )
            .unwrap();
    });
}

// --- Search paths ---

#[divan::bench]
fn search_hybrid(bencher: Bencher) {
    let dir = tempfile::tempdir().unwrap();
    let store = make_store(dir.path());

    let query_tokens = make_tokens(42);
    let token_refs: Vec<&[f32]> = query_tokens.iter().map(|v| v.as_slice()).collect();

    bencher.bench_local(|| {
        let results = store
            .search_multi_with_text(
                black_box("fn benchmark_function impl struct"),
                black_box(&token_refs),
                black_box(10),
                None,
                false,
            )
            .unwrap();
        black_box(results);
    });
}

#[divan::bench]
fn search_semantic(bencher: Bencher) {
    let dir = tempfile::tempdir().unwrap();
    let store = make_store(dir.path());

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
