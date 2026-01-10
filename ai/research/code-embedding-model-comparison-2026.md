# Code Embedding Model Comparison for CLI Search Tools (2026)

**Purpose:** Evaluate embedding models for hygrep/hhg CLI tool where build/index time is the critical adoption factor.

**Summary:** jina-embeddings-v2-base-code (161M) remains the best tradeoff for CLI tools. Larger models (400M-1.5B) offer better quality but 3-10x slower indexing. Quantization and MLX acceleration can close the gap for Apple Silicon users.

---

## Quick Comparison Table

| Model                            | Params | Dims | Context | CoIR Avg | CodeSearchNet | License      | ONNX       | MLX             |
| -------------------------------- | ------ | ---- | ------- | -------- | ------------- | ------------ | ---------- | --------------- |
| **jina-embeddings-v2-base-code** | 161M   | 768  | 8192    | ~55%     | 9/15 top      | Apache 2.0   | Yes (INT8) | Custom JinaBERT |
| SFR-Embedding-Code-400M_R        | 400M   | 1024 | 8192    | 61.9%    | N/A           | CC-BY-NC-4.0 | Yes        | No              |
| Qodo-Embed-1-1.5B                | 1.5B   | 1536 | 32K     | 68.5%    | N/A           | OpenRAIL-M   | No         | No              |
| nomic-embed-code                 | 7B     | 4096 | 2048    | N/A      | 81.7% Py      | Apache 2.0   | No         | No              |
| jina-code-embeddings-1.5b        | 1.5B   | 1536 | 32K     | 79.0%    | N/A           | CC-BY-NC-4.0 | GGUF only  | No              |
| jina-code-embeddings-0.5b        | 494M   | 896  | 32K     | 78.4%    | N/A           | CC-BY-NC-4.0 | GGUF only  | No              |
| CodeRankEmbed-137M               | 137M   | 768  | 8192    | 60.1%    | 78.4% Py      | MIT          | No         | No              |

---

## Detailed Model Analysis

### 1. jinaai/jina-embeddings-v2-base-code (161M) - CURRENT CHOICE

**Specs:**

- Parameters: 161M
- Dimensions: 768
- Context: 8192 tokens (ALiBi extrapolation)
- Architecture: JinaBERT (ALiBi + Gated MLPs + Q/K LayerNorm)
- License: Apache 2.0

**Performance:**

- CoIR average: ~55% (older benchmark)
- CodeSearchNet: 9/15 top positions
- Strong Python, JavaScript, Java, Go, Ruby, PHP support

**Inference Speed (estimated):**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU ONNX INT8 | ~230 | Current hhg default |
| CPU ONNX FP32 | ~80-100 | Before quantization |
| CUDA FP16 | ~500-800 | With tensor cores |
| MLX FP16 | ~2000+ | Custom JinaBERT needed |

**Format Availability:**

- PyTorch: Yes (safetensors)
- ONNX: Yes (nijaru/jina-code-int8)
- Quantized: INT8 ONNX available
- MLX: Requires custom implementation (JinaBERT architecture)

**Recommendation:** Best choice for CLI tools. Small enough for fast indexing, good enough quality, Apache 2.0 licensed, ONNX support.

---

### 2. Salesforce/SFR-Embedding-Code-400M_R (400M)

**Specs:**

- Parameters: 400M
- Dimensions: 1024
- Context: 8192 tokens
- Architecture: E5-style encoder
- License: CC-BY-NC-4.0 (RESEARCH ONLY)

**Performance:**

- CoIR average: 61.9% NDCG@10
- Ranks #3 on CoIR leaderboard (behind 2B and 1.3B models)
- Significantly better than jina-code-v2 on benchmarks

**Inference Speed (estimated):**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU ONNX FP32 | ~40-60 | 2.5x larger than jina |
| CPU ONNX INT8 | ~100-150 | With quantization |
| CUDA FP16 | ~300-500 | Good GPU utilization |

**Format Availability:**

- PyTorch: Yes (safetensors, BF16)
- ONNX: Available on HuggingFace
- Quantized: Would need to create INT8

**Critical Issue:** CC-BY-NC-4.0 license prohibits commercial use. Not viable for hhg.

---

### 3. Qodo/Qodo-Embed-1-1.5B (1.5B)

**Specs:**

- Parameters: 1.5B (based on Qwen2-1.5B)
- Dimensions: 1536
- Context: 32K tokens
- Architecture: Decoder-based (Qwen2)
- License: QodoAI-Open-RAIL-M

**Performance:**

- CoIR average: 68.53% (SOTA for 1.5B class)
- Outperforms OpenAI text-embedding-3-large (65.17%)
- Outperforms Salesforce SFR-2B (67.41%)

**Inference Speed (estimated):**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU FP32 | ~10-20 | Too slow for CLI |
| CPU INT8 | ~30-50 | Still slow |
| CUDA FP16 | ~100-200 | Viable for GPU-only |
| CUDA INT8 | ~200-400 | With TensorRT |

**Format Availability:**

- PyTorch: Yes (safetensors, F32)
- ONNX: Not available
- Quantized: 2 quantized versions on HuggingFace
- MLX: Would require Qwen2 adapter

**Analysis:** Excellent quality but too slow for CLI indexing without GPU. License permits commercial use with attribution.

---

### 4. nomic-ai/nomic-embed-code (7B)

**Specs:**

- Parameters: 7B (based on Qwen2.5-Coder-7B)
- Dimensions: 4096
- Context: 2048 tokens (shorter than others!)
- Architecture: Decoder-based
- License: Apache 2.0

**Performance:**

- CodeSearchNet Python: 81.7% (beats Voyage Code 3)
- CodeSearchNet Java: 80.5%
- Strong multilingual code support

**Inference Speed:**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU | ~2-5 | Impractical |
| CUDA FP16 | ~50-100 | Slow even on GPU |
| CUDA INT4 | ~100-200 | With quantization |

**Format Availability:**

- PyTorch: Yes (safetensors, F32)
- ONNX: No
- Quantized: 8 quantized versions available

**Analysis:** Too large for CLI use. The 2048 context limit is also problematic for code files. Apache 2.0 license is good.

---

### 5. jinaai/jina-code-embeddings-1.5b (1.5B) - NEW 2025

**Specs:**

- Parameters: 1.54B (based on Qwen2.5-Coder-1.5B)
- Dimensions: 1536 (Matryoshka: 128-1536)
- Context: 32K tokens
- Architecture: Decoder with last-token pooling
- License: CC-BY-NC-4.0 (RESEARCH ONLY)

**Performance:**

- Overall average: 79.04% (SOTA)
- MTEB Code average: 78.94%
- Matches voyage-code-3, beats gemini-embedding-001
- Supports 15+ programming languages

**Key Features:**

- Matryoshka dimensions (can truncate to 128 with minimal loss)
- Task-specific prefixes (nl2code, code2code, qa, etc.)
- FlashAttention2 support
- GGUF quantizations available (1-4 bit)

**Inference Speed (estimated):**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU FP32 | ~10-20 | Too slow |
| CPU INT4 (llama.cpp) | ~50-100 | With GGUF |
| CUDA FP16 | ~100-200 | Moderate |
| CUDA INT8 | ~200-400 | With optimization |

**Critical Issue:** CC-BY-NC-4.0 license. Cannot use commercially.

---

### 6. jinaai/jina-code-embeddings-0.5b (494M) - NEW 2025

**Specs:**

- Parameters: 494M (based on Qwen2.5-Coder-0.5B)
- Dimensions: 896 (Matryoshka: 64-896)
- Context: 32K tokens
- Architecture: Decoder with last-token pooling
- License: CC-BY-NC-4.0 (RESEARCH ONLY)

**Performance:**

- Overall average: 78.41%
- Outperforms Qwen3-Embedding-0.6B by 5 points despite being 20% smaller
- Very close to 1.5B quality

**Inference Speed (estimated):**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU FP32 | ~30-50 | Slow |
| CPU INT4 (llama.cpp) | ~100-200 | With GGUF |
| CUDA FP16 | ~200-400 | Reasonable |

**Analysis:** Best quality-to-speed ratio among new models, but CC-BY-NC-4.0 license blocks commercial use.

---

### 7. nomic-ai/CodeRankEmbed (137M)

**Specs:**

- Parameters: 137M
- Dimensions: 768
- Context: 8192 tokens
- Architecture: BERT-based encoder
- License: MIT

**Performance:**

- CoIR average: 60.1%
- CodeSearchNet Python: 78.4%
- Trained with CoRNStack dataset

**Inference Speed (estimated):**
| Backend | Speed (texts/sec) | Notes |
|---------|-------------------|-------|
| CPU FP32 | ~100-150 | Similar to jina |
| CPU INT8 | ~250-300 | Fast |
| CUDA FP16 | ~600-900 | Excellent |

**Format Availability:**

- PyTorch: Yes
- ONNX: Not officially available
- MIT license allows all uses

**Analysis:** Slightly smaller and faster than jina-code-v2, MIT licensed, but lower quality on some benchmarks. Worth considering as alternative.

---

## Inference Speed Benchmarks

### Estimated Throughput by Model Size (128 token inputs)

| Model Size | CPU FP32 | CPU INT8 | CUDA FP16 | MLX FP16 |
| ---------- | -------- | -------- | --------- | -------- |
| ~100-150M  | 100-150  | 230-300  | 600-900   | 2000+    |
| ~400M      | 40-60    | 100-150  | 300-500   | 800-1200 |
| ~500M      | 30-50    | 80-120   | 200-400   | 600-1000 |
| 1.5B       | 10-20    | 30-50    | 100-200   | 300-500  |
| 7B         | 2-5      | 10-20    | 50-100    | 100-200  |

### Quantization Impact (approximate)

| Precision | Speed vs FP32 | Quality Loss |
| --------- | ------------- | ------------ |
| FP16      | 1.5-2x        | ~0%          |
| INT8      | 2-3x          | 0.3-1%       |
| INT4      | 3-5x          | 1-3%         |

---

## Key Questions Answered

### Is 400M or 1.5B model too slow for CLI use?

**Yes, without acceleration.** At ~30-50 texts/sec (400M) or ~10-20 texts/sec (1.5B) on CPU, indexing a 10,000 file codebase would take:

- 400M: 3-5 minutes
- 1.5B: 8-15 minutes
- vs jina-code-v2 INT8: ~45 seconds

**With GPU acceleration:** Becomes viable but requires CUDA or MLX.

### Can larger models be quantized to match smaller model speed?

**Partially.** INT8 quantization gives 2-3x speedup:

- 400M INT8: ~100-150 texts/sec (still 2x slower than jina INT8)
- 1.5B INT8: ~30-50 texts/sec (still 5x slower)

**GGUF Q4:** Can get closer, but quality degradation becomes noticeable for embeddings.

### What's the quality/speed tradeoff curve?

| Model               | Relative Speed  | Quality (CoIR) | Bang for Buck      |
| ------------------- | --------------- | -------------- | ------------------ |
| jina-code-v2 INT8   | 1.0x (baseline) | ~55%           | Best for CLI       |
| CodeRankEmbed       | 1.1x            | 60.1%          | Good alternative   |
| SFR-400M INT8       | 0.5x            | 61.9%          | Limited by license |
| jina-code-0.5b INT4 | 0.4x            | 78.4%          | Limited by license |
| Qodo-1.5B INT8      | 0.2x            | 68.5%          | Needs GPU          |

### Which models have the best "bang for buck"?

1. **jina-embeddings-v2-base-code** - Best overall for CPU CLI
2. **CodeRankEmbed-137M** - MIT licensed alternative, slightly faster
3. **jina-code-embeddings-0.5b** - Best quality, but non-commercial license

---

## License Summary

| Model                        | License      | Commercial Use         |
| ---------------------------- | ------------ | ---------------------- |
| jina-embeddings-v2-base-code | Apache 2.0   | YES                    |
| CodeRankEmbed-137M           | MIT          | YES                    |
| nomic-embed-code             | Apache 2.0   | YES                    |
| nomic-embed-text-v1.5        | Apache 2.0   | YES                    |
| SFR-Embedding-Code-400M_R    | CC-BY-NC-4.0 | NO                     |
| SFR-Embedding-Code-2B_R      | CC-BY-NC-4.0 | NO                     |
| jina-code-embeddings-0.5b    | CC-BY-NC-4.0 | NO                     |
| jina-code-embeddings-1.5b    | CC-BY-NC-4.0 | NO                     |
| Qodo-Embed-1-1.5B            | OpenRAIL-M   | YES (with attribution) |
| Qodo-Embed-1-7B              | Commercial   | PAID                   |

---

## MLX Compatibility

| Model                        | Architecture      | MLX Support                  |
| ---------------------------- | ----------------- | ---------------------------- |
| jina-embeddings-v2-base-code | JinaBERT (custom) | Custom implementation needed |
| CodeRankEmbed-137M           | BERT-based        | Standard BERT should work    |
| nomic-embed-text-v1.5        | BERT-based        | Should work                  |
| Qodo-Embed-1-1.5B            | Qwen2             | MLX-LM has Qwen support      |
| jina-code-0.5b/1.5b          | Qwen2.5-Coder     | MLX-LM has Qwen support      |

**JinaBERT Custom Requirements:**

- ALiBi positional encoding (bidirectional)
- Gated MLPs (GLU-style activation)
- LayerNorm on Q and K in attention
- Pre-norm architecture

---

## Recommendations for hhg

### Short-term (keep current model)

Keep jina-embeddings-v2-base-code with:

1. ONNX INT8 for CPU (~230 texts/sec)
2. ONNX FP16 for CUDA (~500+ texts/sec)
3. Custom MLX JinaBERT for Apple Silicon (~2000+ texts/sec)

### Medium-term (if quality becomes priority)

Consider Qodo-Embed-1-1.5B if:

1. Users have GPU available
2. Quality matters more than indexing speed
3. Can add optional dependency

### Long-term (monitor landscape)

Watch for:

1. Apache 2.0 licensed code embedding models in 400M-1B range
2. ModernBERT-based code embeddings (faster architecture)
3. Better ONNX/MLX support for decoder-based embeddings

---

## Alternative Approaches

### Hybrid Strategy

Use small model (jina-code-v2) for initial indexing, offer reranking with larger model for search:

- Fast index: 230 texts/sec with jina-code-v2
- Quality rerank: jina-reranker-v1-tiny-en on top 20 results

### Matryoshka Dimensions

New models support truncated embeddings (e.g., 128 dims instead of 1536):

- Faster storage and search
- Minimal quality loss (1-2%)
- Could use larger model with smaller embeddings

### Incremental Indexing

Reduce perceived build time by:

- Background indexing after first search
- Incremental updates (already in hhg)
- Progress bar for large builds (already in hhg)

---

## Sources

- [CoIR Leaderboard](https://archersama.github.io/coir/)
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- [Modal: 6 Best Code Embedding Models](https://modal.com/blog/6-best-code-embedding-models-compared)
- [Jina AI: Code Embeddings 0.5B/1.5B](https://jina.ai/news/jina-code-embeddings-sota-code-retrieval-at-0-5b-and-1-5b)
- [Qodo: Qodo-Embed-1](https://www.qodo.ai/blog/qodo-embed-1-code-embedding-code-retrieval/)
- [Sentence Transformers: Speeding up Inference](https://sbert.net/docs/sentence_transformer/usage/efficiency.html)
- [HuggingFace Model Cards](https://huggingface.co/models)

---

_Research date: 2026-01-10_
