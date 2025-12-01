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
    - *Note:* Can be enhanced with **Query Expansion** (LLM generates synonyms) to catch "auth" when searching "login".
- **Rerank:** "The Brain" scores them.
- **UX:** Single entry point.

## 3. Interface (UX)
**Decision:** Single "Magic" Command
- **Command:** `hygrep "query"`
- **Behavior:** The tool automatically performs Recall -> Rerank.
- **Flags:** Optional flags for specific overrides.

## 4. Model Selection
**Decision:** Tiered Strategy
- **Default:** `mixedbread-ai/mxbai-rerank-xsmall-v1`.
- **Format:** ONNX (Quantized).

## 5. Protocol
**Decision:** MCP Native
**Why:** Allows agents to use `hygrep` as a tool.
