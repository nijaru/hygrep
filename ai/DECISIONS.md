# Architectural Decisions

## 1. Language & Runtime
**Decision:** Mojo + MAX Engine
**Why:**
- **Single Binary:** Mojo compiles systems code (grep) and AI graph (rerank) into one static binary.
- **Performance:** Python is too slow for directory walking; Rust is difficult to ship with AI dependencies.
- **Native AI:** MAX Engine allows running quantized models (INT8/FP16) efficiently on CPU/GPU.

## 2. Core Architecture: "Hyper Hybrid" (No Vector DB)
**Decision:** Two-Stage Pipeline: Recall (Keyword/Regex) -> Rerank (Cross-Encoder).
**Alternatives Considered:**
- **Vector DB:** Rejected (Heavy setup/indexing).
- **Pure Grep:** Rejected (No semantic understanding).
**Rationale:**
- **Recall:** "Hyper Scanner" finds candidates.
- **Rerank:** "The Brain" scores them.
- **UX:** Single entry point. The tool determines the best strategy or always runs hybrid.

## 3. Interface (UX)
**Decision:** Single "Magic" Command
- **Command:** `hygrep "query"`
- **Behavior:** The tool automatically performs Recall -> Rerank. No `--smart` flag required for standard semantic behavior.
- **Flags:** Optional flags for specific overrides (e.g., `--literal` to force pure grep speed), but the default is "Best Result".

## 4. Model Selection
**Decision:** Tiered Strategy
- **Default:** `Qwen3-Reranker-0.6B`.
- **Code Fallback:** `bge-reranker-v2-m3`.
- **Format:** ONNX (Quantized).

## 5. Protocol
**Decision:** MCP Native
**Why:** Allows agents to use `hygrep` as a tool.