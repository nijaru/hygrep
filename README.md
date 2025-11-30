# HyperGrep (`hygrep`)

> **The Hybrid Search CLI: `grep` speed, LLM intelligence.**

`hygrep` is a next-generation command-line search tool designed for the AI era. It combines the instant performance of regex-based directory scanning with the semantic understanding of local Large Language Models (LLMs).

**Zero Setup. Zero Indexing. Local Inference.**

## Overview

Traditional search tools force a tradeoff:
*   **`grep`/`ripgrep`:** Fast (<50ms), but limited to literal string matches.
*   **Vector Databases:** Semantic understanding, but require heavy indexing, storage management, and background services.

**HyperGrep** bridges this gap using a **Recall -> Rerank** architecture:
1.  **Hyper Scanner (Recall):** Instantly finds candidate files using high-performance parallel regex (like `ripgrep`).
2.  **The Brain (Rerank):** Uses a local Cross-Encoder model (via MAX Engine) to semantically score candidates against your query.

## Features

*   **Hybrid Search:** Seamlessly blends keyword matching with semantic understanding.
*   **Agent Native:** Implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to serve as a structured tool for AI agents (Claude, IDEs).
*   **Local & Private:** All inference runs locally on your hardware (CPU/GPU). No data leaves your machine.
*   **Single Binary:** Built in Mojo for native performance without Python runtime dependencies.

## Installation

**Prerequisites:**
- [Pixi](https://pixi.sh/) (Package Manager)

```bash
# Clone and build
git clone https://github.com/nijaru/hypergrep
cd hypergrep
pixi install
pixi run build
```

The binary will be available at `./hygrep`.

## Usage

### Just Search
`hygrep` automatically combines keyword scanning and semantic reranking to find the best results.

```bash
# Finds "verify_credentials" even if you search "login logic"
./hygrep "login logic" ./src
```

### Agent Mode (MCP)
Runs as a persistent server for AI agents.
```bash
./hygrep --server
```

## Roadmap

- [ ] **Phase 1: Hyper Scanner** - High-performance parallel directory walker & regex engine.
- [ ] **Phase 2: The Brain** - Integration with MAX Engine and Qwen-Reranker models.
- [ ] **Phase 3: Agent Interface** - Full MCP Server implementation and JSON output.

## License

[MIT](LICENSE)
