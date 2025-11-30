# Mojo & MAX Project Reference

**Based on:** `modular/modular` repository analysis (Nov 29, 2025).

## 1. Project Setup (Pixi)

The standard way to set up a Mojo project with MAX dependencies is using `pixi`.

```toml
[workspace]
name = "hgrep"
version = "0.1.0"
description = "Agent-Native search tool"
authors = ["Your Name <you@example.com>"]
channels = ["conda-forge", "https://conda.modular.com/max-nightly/"]
platforms = ["osx-arm64", "linux-64"]

[dependencies]
max = "*"
python = ">=3.11,<3.14"

[tasks]
build = "mojo build src/main.mojo -o hygrep"
run = "mojo src/main.mojo"
test = "mojo test tests"
```

**Commands:**
- `pixi install`: Install dependencies.
- `pixi run build`: Build the project.
- `pixi run run`: Run the project.

## 2. MAX Engine Architecture

The MAX Engine uses a **Graph-based architecture** where operations are registered via the `@compiler.register` decorator in Mojo.

### Key Components:
1.  **Mojo Graph Operations (`max.kernels`):**
    *   Found in `max/kernels/src/Mogg/MOGGKernelAPI/MOGGKernelAPI.mojo`.
    *   Uses `@compiler.register("mo.op_name")` to bind Mojo functions to Graph ops.
    *   Examples: `mo.add`, `mo.matmul`, `mo.topk`.
2.  **Python Graph API (`max.graph`):**
    *   Constructs the graph in Python, which MAX then executes using the registered Mojo kernels.
    *   **Note:** There is currently **NO public high-level Mojo Graph Construction API**. The "Mojo Native" part is the *kernels* (ops), not the graph *builder*.
3.  **Execution:**
    *   Models are typically loaded/run via `max.engine.InferenceSession` (Python).
    *   For a pure Mojo binary, we must either:
        *   Use **Python Interop** (`from python import Python`) to drive `max.engine`.
        *   Bind to the **C API** (`max/c`) if we want to avoid the Python runtime entirely (advanced, requires manual bindings).

### "Single Static Binary" Reality
Since the high-level Graph API is Python-centric, a "pure Mojo" static binary that *constructs* and *runs* a graph without Python is currently not the standard path in the examples. The "standard" path for MAX + Mojo is:
1.  **Write Custom Kernels** in Mojo (if needed).
2.  **Register them** with `@compiler.register`.
3.  **Run the Graph** via Python (`max.engine`) which calls the compiled Mojo kernels.

**Decision for `hgrep`:**
Since `hgrep` needs to be a CLI tool, we have two options:
A.  **Hybrid:** Use `from python import Python` to load/run the ONNX model via `max.engine`. (Easiest, "Best Bet" for now).
B.  **Pure C-Bind:** Bind `max_c_model_execute` manually. (Harder, but true static binary).

*Recommendation:* Start with **Option A (Python Interop)** for velocity. Switch to Option B if binary size/startup time is critical.

## 3. Directory Structure
Recommended structure for `hgrep`:

```
hgrep/
├── pixi.toml             # Dependencies
├── src/
│   ├── main.mojo         # Entry point
│   ├── scanner/          # "Hyper Scanner" (Mojo)
│   └── brain/            # MAX Integration
│       ├── runner.mojo   # Python Interop to MAX Engine
│       └── reranker.mojo # Rerank logic
├── models/               # ONNX models
└── tests/
```

## 4. Code Examples

### Python Interop (The "Standard" Way)
```mojo
from python import Python

fn rerank(query: String, candidates: List[String]) raises:
    # Import MAX Engine via Python
    var max = Python.import_module("max.engine")
    var session = max.InferenceSession()
    
    # Load model (Qwen/BGE)
    var model = session.load("models/reranker.onnx")
    
    # Execute
    var inputs = ... # Prepare inputs
    var outputs = model.execute(inputs)
```
