# hygrep (hhg)

**Semantic code search with automatic indexing**

```bash
pip install hygrep
hhg "authentication flow" ./src
```

## What it does

Describe what you're looking for in natural language, get relevant code:

```
$ hhg "error handling" ./src
src/api/handler.py:45 function handle_error
  def handle_error(self, exc: Exception) -> Response:
      """Handle API errors and return appropriate response."""
      ...

src/utils/retry.py:12 function with_retry
  def with_retry(func, max_attempts=3):
      """Retry function with exponential backoff on failure."""
      ...
```

## Search Modes

| Mode         | Flag      | Use Case                                     |
| ------------ | --------- | -------------------------------------------- |
| **Semantic** | (default) | Best quality - uses embeddings, auto-indexes |
| **Fast**     | `-f`      | No index needed - grep + neural rerank       |
| **Exact**    | `-e`      | Fastest - literal string match               |
| **Regex**    | `-r`      | Pattern matching                             |

```bash
hhg "auth flow" ./src           # Semantic search (auto-indexes on first run)
hhg -f "auth" ./src             # Grep + neural rerank (instant, no index)
hhg -e "TODO" ./src             # Exact match (fastest)
hhg -r "TODO.*fix" ./src        # Regex match
```

## Install

```bash
pip install hygrep
# or
uv tool install hygrep
# or
pipx install hygrep
```

First search downloads the embedding model (~40MB) and builds an index.

## Usage

```bash
hhg "query" [path]              # Search (default: current dir)
hhg -n 5 "error handling" .     # Limit results
hhg --json "auth" .             # JSON output for scripts/agents
hhg -l "config" .               # List matching files only
hhg -t py,js "api" .            # Filter by file type
hhg --exclude "tests/*" "fn" .  # Exclude patterns
hhg status                      # Check index status
hhg rebuild                     # Rebuild index from scratch
hhg clean                       # Delete index
```

**Note:** Options must come before positional arguments.

## Output

Human-readable (default):

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

Compact JSON (`--json --compact`): Same but without `content` field.

## How it Works

**Default mode (semantic search):**

```
Query → Embed → Vector search → Results
         ↓
    Auto-indexes on first run (.hhg/ directory)
    Auto-updates when files change
```

**Fast mode (`-f`):**

```
Query → Grep scan → Tree-sitter extract → Neural rerank → Results
```

**Exact/Regex mode (`-e`/`-r`):**

```
Pattern → Grep scan → Tree-sitter extract → Results
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
