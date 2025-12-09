# hygrep (hhg)

**Semantic code search with automatic indexing**

```bash
pip install hygrep
hhg build ./src
hhg "authentication flow" ./src
```

## What it does

Search your codebase using natural language. Results are functions and classes ranked by relevance:

```bash
$ hhg build ./src                    # Build index first
Found 40 files (0.0s)
✓ Indexed 646 blocks from 40 files (34.2s)

$ hhg "error handling" ./src         # Then search
api_handlers.ts:127 function errorHandler
  function errorHandler(err: Error, req: Request, res: Response, next: NextFunc...

errors.rs:7 class AppError
  pub enum AppError {
      Database(DatabaseError),

2 results (0.52s)
```

## Why hhg over grep?

grep finds text. hhg finds code.

| Query            | grep finds                | hhg finds                     |
| ---------------- | ------------------------- | ----------------------------- |
| "error handling" | Comments mentioning it    | `errorHandler()`, `AppError`  |
| "authentication" | Strings containing "auth" | `login()`, `verify_token()`   |
| "database"       | Config files, comments    | `Connection`, `query()`, `Db` |

Use grep/ripgrep for exact strings (`TODO`, `FIXME`, import statements).
Use hhg when you want implementations, not mentions.

## Install

Requires Python 3.11-3.13 (onnxruntime lacks 3.14 support).

```bash
pip install hygrep
# or
uv tool install hygrep --python 3.13
# or
pipx install hygrep
```

Models are downloaded from HuggingFace on first use (~40MB).

## Usage

```bash
hhg build [path]                # Build/update index (required first)
hhg "query" [path]              # Semantic search
hhg status [path]               # Check index status
hhg clean [path]                # Delete index

# Options
hhg -n 5 "error handling" .     # Limit results
hhg --json "auth" .             # JSON output for scripts/agents
hhg -l "config" .               # List matching files only
hhg -t py,js "api" .            # Filter by file type
hhg --exclude "tests/*" "fn" .  # Exclude patterns

# Model management
hhg model                       # Check model status
hhg model install               # Download/reinstall models
```

**Note:** Options must come before positional arguments.

## Output

Default:

```
src/auth.py:42 function login
  def login(user, password):
      """Authenticate user and create session."""
      ...
```

JSON (`--json`):

```json
[
  {
    "file": "src/auth.py",
    "type": "function",
    "name": "login",
    "line": 42,
    "end_line": 58,
    "content": "def login(user, password): ...",
    "score": 0.87
  }
]
```

Compact JSON (`--json --compact`): Same fields without `content`.

## How it Works

```
Query → Embed → Vector search (omendb) → Results
         ↓
    Requires 'hhg build' first (.hhg/)
    Auto-updates stale files on search
```

## Supported Languages

Bash, C, C++, C#, Elixir, Go, Java, JavaScript, JSON, Kotlin, Lua, Mojo, PHP, Python, Ruby, Rust, Svelte, Swift, TOML, TypeScript, YAML, Zig

## Development

```bash
git clone https://github.com/nijaru/hygrep && cd hygrep
pixi install && pixi run build-ext && pixi run test
```

## License

MIT
