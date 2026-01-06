# Review: Partial Clean Feature (2026-01-05)

## Files Reviewed

- `/Users/nick/github/nijaru/hygrep/src/hygrep/semantic.py` - `remove_prefix` method (lines 744-782)
- `/Users/nick/github/nijaru/hygrep/src/hygrep/cli.py` - `clean` command (lines 1044-1099)

## Summary

The partial clean feature has **3 bugs** and **2 potential issues** that should be addressed.

---

## Bugs (High Priority)

### 1. Empty Prefix Deletes Everything

**Location:** `/Users/nick/github/nijaru/hygrep/src/hygrep/semantic.py:763`

**Problem:** Empty string prefix matches all files because `"".startswith("")` is always True.

```python
# Line 763
if rel_path == prefix or rel_path.startswith(f"{prefix}/"):
    to_remove.append(rel_path)
```

When `prefix = ""`:

- `rel_path == ""` is False (for any file)
- BUT `rel_path.startswith("/")` is True for any path!

**Impact:** If CLI ever passes empty prefix, entire index is wiped.

**Reproduction:**

```python
idx.remove_prefix("")  # Deletes all files!
```

**Fix:**

```python
def remove_prefix(self, prefix: str) -> dict:
    if not prefix or prefix == ".":
        return {"files": 0, "blocks": 0}  # No-op for empty/current dir
    # ... rest of method
```

### 2. Symlink Resolution Bug in `_to_relative`

**Location:** `/Users/nick/github/nijaru/hygrep/src/hygrep/semantic.py:196-201`

**Problem:** `_to_relative` does not resolve symlinks before computing relative path.

```python
def _to_relative(self, abs_path: str) -> str:
    try:
        return str(Path(abs_path).relative_to(self.root))  # No resolve()!
    except ValueError:
        return abs_path  # Falls back to absolute path
```

**Impact:** On macOS, `/var` is symlink to `/private/var`. If caller passes `/var/...` but `self.root` is `/private/var/...`, the `relative_to` fails and absolute paths are stored in manifest.

**Reproduction:**

```python
# If tempdir returns /var/folders/... but resolved is /private/var/folders/...
idx = SemanticIndex(Path(tmpdir))  # root is /private/var/...
idx.index({"/var/folders/.../file.py": "..."})  # stored as absolute!
```

**Fix:**

```python
def _to_relative(self, abs_path: str) -> str:
    try:
        resolved = Path(abs_path).resolve()
        return str(resolved.relative_to(self.root))
    except ValueError:
        return abs_path
```

### 3. CLI Passes "." Prefix When Path == Parent

**Location:** `/Users/nick/github/nijaru/hygrep/src/hygrep/cli.py:1070`

**Problem:** When `path.relative_to(parent)` equals `"."` (same directory), this is passed to `remove_prefix(".")` which correctly matches nothing. But this is confusing UX - user expects "remove my path from parent" but gets "No blocks found".

```python
rel_prefix = str(path.relative_to(parent))  # Returns "." when path == parent
index = SemanticIndex(parent)
stats = index.remove_prefix(rel_prefix)  # remove_prefix(".") matches nothing
```

**Impact:** User confusion. When user runs `hhg clean .` in an indexed subdir without its own index, they expect partial removal but get "No blocks found".

**Note:** This is low priority since `find_parent_index` starts from parent, so it won't find an index at the same location. But the logic is still confusing.

---

## Potential Issues (Medium Priority)

### 4. No Transaction Safety for Partial Delete

**Location:** `/Users/nick/github/nijaru/hygrep/src/hygrep/semantic.py:769-780`

**Problem:** If `db.delete()` fails partway through, manifest may be out of sync with database.

```python
for rel_path in to_remove:
    # ...
    db.delete(block_ids)       # What if this fails?
    manifest["files"].pop(...)  # This still runs

db.flush()
self._save_manifest(manifest)  # Manifest updated even if delete partially failed
```

**Impact:** Orphaned blocks in database (blocks in db but not in manifest).

**Mitigation:** omendb has internal locking that prevents concurrent corruption. The issue is partial failure during delete, but `db.delete()` seems to handle missing IDs gracefully (returns 0 for nonexistent).

### 5. Old Manifest Format Raises on Any Operation

**Location:** `/Users/nick/github/nijaru/hygrep/src/hygrep/semantic.py:243-247`

**Problem:** For v4 manifests, `_load_manifest` raises RuntimeError. This blocks `remove_prefix` even though the user might want to just clean up the old index.

```python
if version < 5 and files:
    raise RuntimeError(
        "Index was built with an older embedding model.\n"
        "Rebuild with: hhg build --force"
    )
```

**Impact:** User cannot use `remove_prefix` or `clean` on old indexes - they must rebuild first.

**Suggestion:** Allow clean operations on old indexes (just delete the whole thing instead of partial).

---

## Edge Cases Verified (Working Correctly)

| Case                           | Behavior                    | Status        |
| ------------------------------ | --------------------------- | ------------- |
| Prefix "."                     | Matches nothing             | OK            |
| Path traversal "../"           | Matches nothing             | OK            |
| Corrupted manifest JSON        | Raises JSONDecodeError      | OK (expected) |
| Concurrent access              | omendb has internal locking | OK            |
| `db.delete()` with missing IDs | Returns 0, no error         | OK            |

---

## Recommendations

1. **Fix empty prefix bug** - Add guard at start of `remove_prefix`
2. **Fix symlink resolution** - Call `.resolve()` in `_to_relative`
3. **Improve CLI UX** - When `rel_prefix == "."`, show better message
4. **Add tests** for edge cases (empty prefix, symlinks, path traversal)

---

## Test Results

All existing tests pass:

```
pixi run test
# All 4 Mojo tests pass
# All Python tests pass (semantic, cli, golden, languages, scanner_fallback)
```

Edge case tests reveal the bugs documented above.
