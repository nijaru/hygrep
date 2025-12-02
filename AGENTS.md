# HyperGrep (hygrep)

**Hybrid search CLI: grep speed + LLM intelligence. Stateless, no indexing.**

## Quick Reference

```bash
pixi run build                      # Build binary
pixi run test                       # Run tests
pixi run ./hygrep "query" ./src     # Search
pixi run ./hygrep "query" . --json  # Agent output
```

## Architecture

```
Query → [Recall: Mojo Scanner] → candidates → [Rerank: ONNX] → results
              ↓                                    ↓
        Parallel regex                    Tree-sitter extraction
        ~20k files/sec                    Cross-encoder scoring
```

| Stage | Constraint | Implementation |
|-------|------------|----------------|
| Scanner | Pure Mojo/C, no Python | `src/scanner/walker.mojo` + `c_regex.mojo` |
| Extraction | Tree-sitter AST | `src/inference/context.py` |
| Reranking | <200ms latency | `src/inference/bridge.py` (ONNX batched) |

## Project Structure

```
src/
├── scanner/
│   ├── walker.mojo      # Parallel directory traversal
│   ├── c_regex.mojo     # POSIX regex FFI (libc)
│   └── py_regex.mojo    # Python regex fallback (unused)
├── inference/
│   ├── reranker.mojo    # Python bridge wrapper
│   ├── bridge.py        # ONNX inference + orchestration
│   └── context.py       # Tree-sitter extraction
cli.mojo                 # Entry point
tests/                   # Mirrors src/ structure
models/                  # ONNX models (gitignored, auto-downloaded)
ai/                      # Session context
```

## Technology Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Mojo | 25.7.* | Via MAX package |
| Python | >=3.11, <3.14 | Interop for inference |
| ONNX Runtime | >=1.16 | Model execution |
| Tree-sitter | >=0.24 | AST parsing (6 languages) |
| Model | mxbai-rerank-xsmall-v1 | INT8 quantized, ~40MB |

## Mojo Patterns (from modular/stdlib)

### FFI for C Interop

```mojo
# Use sys.ffi types for C compatibility
from sys.ffi import c_char, c_int, external_call

# Proper external_call signature
fn regcomp(
    preg: UnsafePointer[regex_t],
    pattern: UnsafePointer[c_char],
    cflags: c_int,
) -> c_int:
    return external_call["regcomp", c_int](preg, pattern, cflags)
```

### Memory Management

```mojo
# Always pair alloc with free (use defer for safety)
var buffer = alloc[UInt8](size)
defer: buffer.free()

# Initialize allocated memory explicitly
for i in range(size):
    buffer[i] = 0
```

### Error Handling

```mojo
# Use raises for recoverable errors
fn scan_directory(path: Path) raises -> List[Path]:
    if not path.exists():
        raise Error("Path does not exist: " + String(path))
    # ...
```

### Parallel Patterns

```mojo
# Use @parameter for worker functions
@parameter
fn worker(i: Int):
    result[i] = process(items[i])

parallelize[worker](num_items)
```

## Code Standards

| Aspect | Standard |
|--------|----------|
| Formatting | `mojo format` (automatic) |
| Imports | stdlib → external → local |
| Functions | Docstrings on public APIs |
| Memory | Explicit cleanup, no leaks |
| Errors | `raises` for recoverable, `abort` for fatal |

## Verification

| Check | Command | Pass Criteria |
|-------|---------|---------------|
| Build | `pixi run build` | Zero errors |
| Test | `pixi run test` | All pass |
| Smoke | `./hygrep "test" ./src` | Returns results |

## Known Limitations

| Issue | Impact | Status |
|-------|--------|--------|
| Circular symlinks | Infinite loop | Open |
| 128-byte regex leak | Negligible for CLI | Mojo v25.7 limitation |
| Python version coupling | Hardcoded 3.11-3.13 | Needs fix |

## AI Context

**Read order:** `ai/STATUS.md` → `ai/DECISIONS.md` → `ai/ROADMAP.md`

| File | Purpose |
|------|---------|
| `ai/STATUS.md` | Current state, blockers |
| `ai/DECISIONS.md` | Architectural decisions |
| `ai/ROADMAP.md` | Phases, milestones |
| `ai/research/` | External research |

## External References

- Mojo stdlib patterns: `~/github/modular/modular/mojo/stdlib/`
- FFI examples: `stdlib/sys/ffi.mojo`, `stdlib/sys/_libc.mojo`
- Memory safety: `stdlib/memory/unsafe_pointer.mojo`
