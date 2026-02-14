# hhg (hybrid grep)

**Semantic code search — understands what you're looking for**

```bash
cargo install --path .
hhg build ./src
hhg "authentication flow" ./src
```

## What it does

Search code using natural language. Combines multi-vector semantic embeddings with BM25 keyword matching for accurate results:

```bash
$ hhg build ./src
Found 69 files (0.0s)
Indexed 801 blocks from 69 files (10.8s)

$ hhg "error handling" ./src
src/cli/search.rs:42 function handle_search
  pub fn handle_search(args: &SearchArgs) -> Result<()> {

src/types.rs:15 enum SearchError
  pub enum SearchError {
      IndexNotFound,

2 results (0.27s)
```

## Why hhg over grep?

grep finds exact text. hhg understands what you're looking for.

| Query            | grep finds                | hhg finds                     |
| ---------------- | ------------------------- | ----------------------------- |
| "error handling" | Comments mentioning it    | `errorHandler()`, `AppError`  |
| "authentication" | Strings containing "auth" | `login()`, `verify_token()`   |
| "database"       | Config files, comments    | `Connection`, `query()`, `Db` |

**Hybrid search** combines multi-vector semantic embeddings (ColBERT-style token matching via MuVERA) with BM25 keyword matching. Best of both worlds.

Use grep/ripgrep for exact strings (`TODO`, `FIXME`, import statements).
Use hhg when you want implementations, not mentions.

## Install

Requires Rust nightly toolchain.

```bash
git clone https://github.com/nijaru/hygrep && cd hygrep
cargo install --path .
```

The embedding model downloads on first use (~17MB).

## Usage

```bash
hhg build [path]                # Build/update index (required first)
hhg "query" [path]              # Semantic search
hhg file.rs#func_name           # Find similar code (by name)
hhg file.rs:42                  # Find similar code (by line)
hhg status [path]               # Check index status
hhg list [path]                 # List all indexes under path
hhg clean [path]                # Delete index
hhg clean [path] -r             # Delete index and all sub-indexes

# Options
hhg -n 5 "error handling" .     # Limit results
hhg --json "auth" .             # JSON output for scripts/agents
hhg -l "config" .               # List matching files only
hhg -t py,js "api" .            # Filter by file type
hhg --exclude "tests/*" "fn" .  # Exclude patterns
```

## How it Works

```
Build:  Scan (gitignore-aware) -> Extract (tree-sitter AST) -> Embed (ONNX, 48d/token) -> Store (omendb multi-vector + BM25)
Search: Embed query -> Hybrid search (BM25 candidates + MuVERA MaxSim rerank) -> Code-aware boost -> Results
```

- **Multi-vector embeddings:** Each code block gets per-token embeddings (ColBERT-style), not a single vector. Token-level matching captures structural patterns that CLS pooling loses.
- **MuVERA:** Compresses variable-length token sequences into fixed-dimensional encodings for HNSW index, then MaxSim reranks candidates for precise scoring.
- **BM25 pre-filtering:** tantivy-based keyword search generates candidates cheaply, avoiding brute-force comparison across all blocks.
- **Code-aware boost:** Post-search heuristics for identifier matching (camelCase/snake_case splitting, exact name match, type-aware ranking).

All running on CPU with INT8 quantized embeddings. No GPU, no server, just a local binary.

Built on [omendb](https://github.com/nijaru/omendb).

## Supported Files

**Code** (25 languages): Bash, C, C++, C#, CSS, Elixir, Go, HCL, HTML, Java, JavaScript, JSON, Kotlin, Lua, PHP, Python, Ruby, Rust, Swift, TOML, TypeScript, YAML, Zig

**Text**: Markdown, plain text — smart chunking with header context

## License

MIT
