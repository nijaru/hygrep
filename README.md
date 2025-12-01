# HyperGrep (`hygrep`)

> **The Hybrid Search CLI: `grep` speed, LLM intelligence.**

`hygrep` is a next-generation command-line search tool designed for developers and AI agents alike. It combines the instant performance of regex-based directory scanning with the semantic understanding of local Large Language Models (LLMs).

**Zero Setup. Zero Indexing. Local Inference.**

## Why HyperGrep?

Traditional tools force you to choose:
*   **`grep`:** Fast, but dumb. It only finds exact text matches.
*   **AI Search:** Smart, but slow. It usually requires you to wait for "indexing" before you can search anything.

**HyperGrep gives you both:**
1.  **It scans fast:** We use a high-performance scanner to find files that *might* match your query (using keywords/regex).
2.  **It thinks smart:** We use a local AI model to read those files and rank them by how well they actually answer your question.

**No database. No waiting for indexing. Just run it.**

## Features

*   **Human Friendly:** You get the speed of a CLI tool with the intelligence of an AI assistant.
*   **Hybrid Search:** Seamlessly blends keyword matching with semantic understanding.
*   **Agent Ready:** Can also act as a tool for AI agents (like Claude) to search your codebase.
*   **Local & Private:** All AI runs locally on your machine. Your code never leaves your laptop.
*   **Single Binary:** Easy to install, no Python dependencies required.

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

## Roadmap

- [ ] **Phase 1: Hyper Scanner** - High-performance parallel directory walker & regex engine.
- [ ] **Phase 2: The Brain** - Integration with ONNX Runtime and Mixedbread Reranker.
- [ ] **Phase 3: CLI Polish** - Robust flags, JSON output, and professional UX.

## License

[MIT](LICENSE)
