# Full Codebase Review: omengrep

**Date:** 2026-02-23
**Scope:** All Rust source (src/, benches/, tests/), recent optimization sprint (d999b97..e31a661)
**Build:** Clean (nightly-2025-12-04). Tests: 26/26 pass.

## Critical (must fix)

### 1. String truncation at byte boundary can panic on multi-byte UTF-8

`/Users/nick/github/nijaru/omengrep/src/cli/output.rs:101`

```rust
let truncated = if line.len() > 80 {
    format!("{}...", &line[..77])
```

`line[..77]` indexes into bytes. If byte 77 lands in the middle of a multi-byte UTF-8 character (CJK code, emoji, accented characters), this panics at runtime with `byte index 77 is not a char boundary`.

Fix:

```rust
let truncated = if line.len() > 80 {
    let end = line.floor_char_boundary(77);
    format!("{}...", &line[..end])
```

`floor_char_boundary` is nightly-only. Stable alternative:

```rust
fn truncate_str(s: &str, max_bytes: usize) -> &str {
    if s.len() <= max_bytes { return s; }
    let mut end = max_bytes;
    while end > 0 && !s.is_char_boundary(end) { end -= 1; }
    &s[..end]
}
```

**Confidence:** 95% -- any file with non-ASCII content triggers this.

### 2. MCP search uses full scan (walker::scan) instead of metadata-only scan

`/Users/nick/github/nijaru/omengrep/src/cli/mcp.rs:212`

```rust
let files = walker::scan(&index_root).map_err(|e| json_rpc_error(-32000, &e.to_string()))?;
let stale = idx.needs_update(&files) ...
if stale > 0 { idx.update(&files) ... }
```

The CLI search path (`cli/search.rs:81-82`) uses the fast `scan_metadata` + `check_and_update` path that only stats files and reads content for changed ones. The MCP path reads ALL file contents upfront via `walker::scan`, defeating the optimization. For a large codebase, this is the difference between milliseconds and seconds per MCP call.

Fix: Use the same fast path as CLI search.

```rust
let metadata = walker::scan_metadata(&index_root).map_err(...)?;
let (stale_count, _stats) = idx.check_and_update(&metadata).map_err(...)?;
```

**Confidence:** 95%

### 3. Double manifest load in `update()` -- stale manifest races

`/Users/nick/github/nijaru/omengrep/src/index/mod.rs:557-596`

```rust
pub fn update(&self, files: &HashMap<PathBuf, (String, u64)>) -> Result<IndexStats> {
    let manifest = Manifest::load(&self.index_dir)?;       // Load #1
    let (changed, deleted) = self.get_stale_files_with_manifest(files, &manifest);
    ...
    {
        let mut store = self.open_store()?;
        let mut manifest = Manifest::load(&self.index_dir)?;  // Load #2 (shadow!)
        for rel_path in &deleted { ... manifest.files.remove(rel_path) ... }
        manifest.save(&self.index_dir)?;
    }
    let mut stats = self.index(&changed_files, None)?;  // index() loads manifest AGAIN
```

The second `Manifest::load` at line 573 shadows the first. If `self.index()` (called at line 596) also loads and saves the manifest, the delete operations from the scoped block are potentially overwritten by `self.index()` which loads its own copy.

Looking at `index()` (line 74-234): it does `Manifest::load` at line 80, then saves at line 228. So the flow is:

1. Load manifest, find deleted files
2. Load manifest again, remove deleted entries, save
3. `self.index()` loads manifest (now without deleted), adds changed, saves

This actually works because step 2 saves before step 3 loads. But it's fragile and loads the manifest 3 times. The `check_and_update` method (line 470) does this correctly with a single manifest load.

Fix: Restructure `update()` to follow the `check_and_update` pattern -- single manifest load, handle deletes, then pass the modified manifest through.

**Confidence:** 85% (works today but fragile)

## Important (should fix)

### 4. `extract_name` traverses only 2 levels, misses some language patterns

`/Users/nick/github/nijaru/omengrep/src/extractor/mod.rs:186-224`

The function searches direct children then grandchildren for name-bearing nodes. Some languages (e.g., decorated Python functions, Rust `pub(crate) async fn`) may have identifiers at depth 3+. This results in blocks named "anonymous" that harm search quality.

Currently this is partially mitigated by `decorated_definition` being captured as `@function` in the Python query, but other languages may have similar patterns.

**Confidence:** 80%

### 5. Keyword stop-list comparison is case-sensitive vs. split_word output is lowercased

`/Users/nick/github/nijaru/omengrep/src/tokenize.rs:148-165`

```rust
pub fn split_identifiers(text: &str) -> String {
    ...
    for mat in IDENT_RE.find_iter(text) {
        let word = mat.as_str();
        if word.len() < 4 { continue; }
        if KEYWORD_STOP_LIST.contains(&word) {  // matches "impl", "self", etc. as-is
            continue;
        }
        let parts = split_word(word);
        for part in parts {
            if !KEYWORD_STOP_LIST.contains(&part.as_str()) {  // parts are lowercased
```

The `word` check (line 157) is case-sensitive against the lowercased stop-list. So `Impl`, `Self`, `Return` etc. would NOT be filtered as whole words. Since `split_word` lowercases its output, the inner check (line 161) correctly catches split parts. The pre-split whole-word check only misses PascalCase keywords, which are rare but possible (Kotlin `When`, Swift `Self`).

**Confidence:** 80% -- minor quality impact

### 6. `find_similar` search_k calculation may over-allocate

`/Users/nick/github/nijaru/omengrep/src/index/mod.rs:345`

```rust
let search_k = k.saturating_mul(3).saturating_add(entry.blocks.len());
```

For a file with 100 blocks and k=10, search_k = 130. For a file with 1000 blocks, search_k = 1030. The blocks.len() term is meant to ensure we over-fetch past same-file results, but adding the full block count is excessive -- we only need to skip blocks from the reference file.

**Confidence:** 75% -- functionally correct, just wasteful

### 7. `scan_metadata` and `scan` duplicate filtering logic

`/Users/nick/github/nijaru/omengrep/src/index/walker.rs`

Both `scan_metadata()` (lines 80-136) and `scan()` (lines 150-222) have identical file-filtering logic (hidden files, binary extensions, lock files). Any change to one must be replicated in the other.

Fix: Extract shared predicate function:

```rust
fn should_skip(path: &Path) -> bool {
    // hidden file check, binary extension check, lock json check
}
```

**Confidence:** 95%

### 8. Markdown fence matching does not track fence character

`/Users/nick/github/nijaru/omengrep/src/extractor/text.rs:200-231`

The fence regex `^(\`{3,}|~{3,})(\w+)?` captures the opener but the closer check (`fence_re.captures(line)`) matches any fence, not the matching one. So a document with:

    ~~~python
    code with ``` inside
    ~~~

would incorrectly close the block at the triple-backtick line inside the code block.

Fix: Store the opening fence string and match the closer against it.

**Confidence:** 90%

### 9. `check_and_update` re-stats files after `scan_metadata` already did

`/Users/nick/github/nijaru/omengrep/src/index/mod.rs:486`

```rust
let mtime = walker::file_mtime(path);
```

The caller (`cli/search.rs:81`) already has mtimes from `scan_metadata`. These are passed to `check_and_update` but then discarded -- the method re-stats each changed file. The metadata HashMap should be used to avoid the redundant stat calls.

Fix: Use the mtime from the metadata map instead of re-statting:

```rust
let mtime = metadata.get(path).map(|&(_size, mt)| mt).unwrap_or(0);
```

**Confidence:** 90%

## Uncertain (verify)

### 10. Race window between mtime check and content read

`/Users/nick/github/nijaru/omengrep/src/index/mod.rs:484-504` and `/Users/nick/github/nijaru/omengrep/src/index/walker.rs:197-218`

The comment says "Stat before read so mtime is never newer than the content we index." This is correct -- if the file is modified after the stat but before the read, we get newer content with an older mtime, so on the next check we'll re-index (safe). But if the file is modified after the read, we stored old content with an old mtime that won't trigger re-indexing until the next modification. This is inherent to non-locking file access and acceptable.

**Confidence:** 70% this is worth mentioning; the mitigation is correct.

### 11. HTML element extraction may produce too many blocks

`/Users/nick/github/nijaru/omengrep/src/extractor/queries.rs:161-166`

```
"html" => {
    r#"
    (element) @element
    (script_element) @script
    (style_element) @style
    "#
}
```

Every `<div>`, `<p>`, `<span>` is an `element`. A typical HTML file would produce hundreds of blocks. The `remove_nested_blocks` function helps (drops outer containers), but `element` is not in `CONTAINER_TYPES`, so nested divs would all be kept.

**Confidence:** 75%

### 12. `Extractor` parser cache grows unbounded

`/Users/nick/github/nijaru/omengrep/src/extractor/mod.rs:17-19`

```rust
pub struct Extractor {
    parsers: std::collections::HashMap<String, (Parser, Language, Option<Query>)>,
}
```

One entry per unique extension. Maximum ~30 entries (all supported languages). Not a real problem in practice.

**Confidence:** 60% -- not a real issue

## Summary

| Severity  | Count | Key Issues                                                          |
| --------- | ----- | ------------------------------------------------------------------- |
| Critical  | 3     | UTF-8 panic in output, MCP perf regression, double manifest load    |
| Important | 6     | Walker duplication, fence matching, redundant stat, name extraction |
| Uncertain | 3     | Race windows, HTML over-extraction, parser cache                    |

The codebase is well-structured with clean module boundaries. The optimization sprint (mtime pre-check, PreparedBlock, nested dedup, BM25 stop-words) is correctly implemented. The main risks are the UTF-8 panic (data-dependent crash) and the MCP path not using the fast scan optimization.
