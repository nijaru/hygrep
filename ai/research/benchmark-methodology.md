# Code Search Benchmark Methodology

**Researched:** 2026-02-21

## Summary

Two orthogonal problems: correctness (recall/MRR) and performance (throughput/latency). Standard academic benchmarks cover correctness well. Performance benchmarks for local CLI tools are sparse — ripgrep's methodology is the best template. A practical omengrep benchmark needs both.

---

## 1. ColGrep (LightOn, Feb 2026)

**Source:** https://www.lighton.ai/lighton-blogs/lateon-code-colgrep-lighton

### How They Measure

ColGrep evaluates via a **QA task over real repos**, not a standard IR benchmark. They use Claude Opus 4.5 as a judge: run the same agent question with grep vs. ColGrep, compare answer quality.

**Setup:**

- 135 code retrieval questions, 3 difficulty levels (Easy / Medium / Hard)
- Test repos: Datasets, Accelerate, Optimum, Transformers, TRL
- Baseline: keyword grep (lexical) and BM25

**Metrics reported:**

- Win rate: 70% (ColGrep answer rated better by judge)
- Token savings: 60,000 tokens/query on complex questions, 15.7% overall
- Search operations: 56% fewer than grep baseline
- Per-difficulty win rates: ~65% (Easy), ~69% (Hard)

**MTEB Code benchmark (model quality):**

- LateOn-Code 17M: 66.64 average score
- LateOn-Code 130M: 74.12 average score
- BM25 baseline: 44.41
- Competitors (granite, Gemma variants): lower scores at larger parameter counts

### Weaknesses

- QA win-rate is end-to-end and model-dependent (judge model matters)
- TRL repo was noted as exception where grep outperformed — not hidden
- No latency or indexing throughput numbers published
- No recall@k or MRR against ground-truth relevance labels

---

## 2. Standard Correctness Benchmarks

### CodeSearchNet (GitHub/Microsoft, 2019 — still active)

**Source:** https://arxiv.org/pdf/1909.09436 | https://github.com/github/CodeSearchNet

- **Corpus:** ~6M functions from GitHub, 6 languages (Go, Java, JS, PHP, Python, Ruby)
- **Annotated set:** 99 NL queries, ~4k expert relevance annotations
- **Metric:** MRR (Mean Reciprocal Rank), NDCG@k
- **Task:** NL query -> ranked list of functions
- Archived Apr 2023 but dataset and methodology are canonical reference

### CoSQA / CoSQA+ (Microsoft, 2021 / Sun Yat-sen, 2024-2025)

**Source:** https://arxiv.org/html/2406.11589v7

- **Corpus:** 20,604 NL query–Python function pairs (CoSQA), multi-match version (CoSQA+)
- **Queries:** Real web search queries (Bing), not docstrings — more realistic
- **Annotation:** At least 3 human annotators per pair; CoSQA+ adds LLM-based annotation + functional test verification
- **Metrics:** MRR, Recall@k, Accuracy (multi-choice)
- **Key improvement in CoSQA+:** Multi-choice framing (one query may have multiple valid code matches), test-driven verification so annotations are functionally correct

### CoIR (Huawei Noah's Ark, ACL 2025)

**Source:** https://arxiv.org/html/2407.02883v3 | https://github.com/CoIR-team/coir

The most comprehensive current benchmark.

- **10 datasets**, 8 tasks, 7 domains, 14 programming languages
- **Primary metric:** NDCG@10 (also MAP, Recall, Precision available)
- **Tasks:** Text-to-Code, Code-to-Text, Code-to-Code, Hybrid Code (StackOverflow QA)

| Dataset                | Task         | Size (test) |
| ---------------------- | ------------ | ----------- |
| APPS                   | Text-to-Code | 3,800       |
| CoSQA                  | Text-to-Code | 500         |
| Synthetic Text2SQL     | Text-to-Code | 6,000       |
| CodeSearchNet          | Code-to-Text | 53,000      |
| CodeSearchNet-CCR      | Code-to-Code | 53,000      |
| CodeTransOcean-DL      | Code-to-Code | 180         |
| CodeTransOcean-Contest | Code-to-Code | 446         |
| StackOverflow QA       | Hybrid       | 2,000       |
| CodeFeedback-ST        | Hybrid       | 31,000      |
| CodeFeedback-MT        | Hybrid       | 13,000      |

- Python framework, pip installable, same schema as MTEB/BEIR
- Top results: Voyage-Code-002 (56.26 avg NDCG@10), E5-Mistral (55.18)
- No single model dominates all tasks

### AdvTest (CodeBERT era, in CodeXGLUE)

**Source:** NeurIPS 2021 CodeXGLUE paper

- Adversarial variant of CodeSearchNet (Python subset)
- Queries modified to break surface-form overlap, test true semantic understanding
- Used to probe robustness, not a primary leaderboard
- Metric: MRR

### MTEB Code (2024-2025)

- Part of MTEB v2 (released Oct 2025)
- Code retrieval tasks alongside NLP tasks
- LightOn uses this as their primary model quality benchmark
- LateOn-Code-edge INT8 (17M) scores 66.64

---

## 3. Performance Benchmarks — Lexical Tools

### Ripgrep Benchmark (Andrew Gallant, 2016 — canonical methodology)

**Source:** https://burntsushi.net/ripgrep/

The best published methodology for CLI search tool benchmarking.

**Corpora:**

- Linux kernel source (built checkout, commit d0acc7) — ~gigabytes of real code with build artifacts
- OpenSubtitles2016 English (~1GB) and Russian (~1.6GB) for single-file tests

**Metrics:**

- Wall-clock time (mean ± std dev over 10 runs)
- Line count (correctness check)
- Memory usage (secondary)

**25 benchmarks total:**

- 11 code search on Linux repo
- 6 single-file (subtitle datasets)
- 4 edge cases (Unicode, PCRE2, etc.)

**Methodology for reproducibility:**

- Warmup: 3 runs before measurement
- Measurement: 10 timed runs, report distribution
- Baselines: GNU grep, git grep, ag (Silver Searcher), ucg, pt, sift
- Full benchmark runner provided as Python script with corpus download
- EC2 instance + local machine both documented
- Raw data published

**Key finding:** Memory-mapped I/O is _slower_ for many-file search; parallel thread search wins.

### Zoekt (Sourcegraph, trigram-based)

Zoekt benchmarks internally against index size and query latency. No published methodology. Uses trigram + symbol ranking. Tested at "thousands of repositories" scale for Sourcegraph enterprise. Relevant metrics: index build time, query latency under concurrent load.

### Sourcegraph (internal)

- Incremental indexing: reduced from 36 min to 9 min per commit (+75%)
- Memory benchmarks via cAdvisor container_memory_working_set_bytes
- No published correctness benchmarks — purely operational performance

---

## 4. Performance Metrics That Matter

### Correctness

| Metric   | Definition                                          | Notes                                           |
| -------- | --------------------------------------------------- | ----------------------------------------------- |
| Recall@k | Fraction of relevant results in top-k               | k=1, 5, 10 typical                              |
| MRR      | Mean reciprocal rank of first correct result        | Standard for single-answer queries              |
| NDCG@k   | Graded relevance, discounted by rank                | Preferred when relevance is graded (not binary) |
| MAP      | Mean Average Precision                              | Integrates precision across all recall levels   |
| Win rate | % of queries where tool beats baseline (LLM-judged) | ColGrep style, end-to-end but noisy             |

For omengrep: **MRR and Recall@10** are the right primary metrics. NDCG@10 if we can get graded relevance labels.

### Performance

| Metric               | Definition                      | Notes                                    |
| -------------------- | ------------------------------- | ---------------------------------------- |
| Indexing throughput  | blocks/sec or files/sec         | Measure at p50 and report total time     |
| Index size           | MB per 1000 blocks              | Storage efficiency                       |
| Search latency p50   | Median query time               | Cold cache vs warm cache                 |
| Search latency p99   | 99th percentile                 | Tail behavior under load                 |
| Search latency p999  | 99.9th percentile               | SeekStorm reports this for phrase search |
| QPS                  | Queries per second (concurrent) | More relevant for server tools than CLI  |
| Time-to-first-result | Latency before first output     | UX metric for streaming                  |

ANN-Benchmarks standard: plot **recall vs. QPS** as a tradeoff curve. This is the right framing for semantic search where you trade accuracy for speed.

VectorDBBench metrics: Max load count (capacity), QPS (peak), Recall (accuracy).

---

## 5. Standard Corpora for Benchmarking

### For correctness (existing labeled datasets)

| Corpus             | Size                             | Languages                       | Annotation            | Use                    |
| ------------------ | -------------------------------- | ------------------------------- | --------------------- | ---------------------- |
| CodeSearchNet      | 6M functions, 99 queries labeled | Go, Java, JS, PHP, Python, Ruby | Expert (4k pairs)     | MRR/NDCG baseline      |
| CoSQA              | 20,604 pairs                     | Python                          | 3 human annotators    | MRR, realistic queries |
| CoIR (10 datasets) | Varies (180-53k test)            | 14 languages                    | Mixed human/automated | NDCG@10, comprehensive |
| APPS               | 3,800 test                       | Python                          | Functional tests      | Text-to-code accuracy  |

### For performance (real codebases as index targets)

| Corpus                            | Size              | Why it's good                        |
| --------------------------------- | ----------------- | ------------------------------------ |
| Linux kernel                      | ~gigabytes, built | Realistic, consistent, well-known    |
| CPython                           | ~300k LOC         | Python, clean, well-structured       |
| Rust std + tokio + serde          | Variable          | Rust, multi-crate realistic workload |
| torvalds/linux at specific commit | Pinned            | Reproducible                         |
| omengrep's own source + deps      | ~small            | Smoke test, always available         |

For omengrep specifically: the Linux kernel at a pinned commit is the best performance benchmark corpus because it is large, diverse in file types, and enables comparison across tools.

### Synthetic corpora

- Cursor internal benchmark: repos averaging 92% similarity across developer clones (relevant for incremental indexing)
- ANN-Benchmarks datasets: glove-100, sift-128, nytimes-256 (for pure vector search, not code-specific)
- Augment Code: "thousands of files/second" claimed but no corpus specified

---

## 6. Practical Benchmark Design for omengrep

### Correctness Benchmark

**Dataset:** CoSQA (500 test queries, Python, realistic NL queries) and/or CodeSearchNet Ruby subset (smaller, diverse)

**Protocol:**

1. Build index on CodeSearchNet corpus (Python or Ruby subset)
2. Run all test queries, collect ranked results
3. Compute MRR and Recall@1, Recall@5, Recall@10 against ground truth
4. Compare: BM25-only, semantic-only, hybrid (current), +boost vs -boost

**Why CoSQA:** Queries come from real web searches ("how to read a file in python"), not docstrings. More realistic than CodeSearchNet's auto-mined queries.

### Performance Benchmark

**Corpora:** Linux kernel at pinned commit (large) + omengrep source (small, always available)

**Indexing protocol:**

1. Cold start (no cache), build index
2. Measure total wall time, blocks extracted, blocks embedded
3. Compute: blocks/sec, files/sec
4. Repeat 3x, report mean ± std
5. Report: index size on disk, peak RSS

**Search protocol (following ripgrep methodology):**

1. 3 warmup runs
2. 10 timed runs per query
3. Report p50, p99 latency
4. Query set: 20 representative queries (mix of NL and identifier-style)
5. Compare: cold index load vs warm (in-memory)

**Baselines:**

- ripgrep (lexical, no semantics)
- ColGrep (same model family, different vector DB)
- BM25-only mode (og with --bm25-only if implemented)

### Recall vs. Latency Tradeoff

Following ANN-Benchmarks convention: vary the number of BM25 candidates fed to reranker (current default unknown), plot Recall@10 vs. p50 latency. This shows where the quality/speed knee is.

---

## 7. Key Findings and Gaps

**What ColGrep does well:** End-to-end QA evaluation is more practical than IR metrics for measuring agent utility. Token savings and win rate are business-relevant metrics.

**What ColGrep doesn't publish:** Indexing throughput, search latency, recall@k against labeled ground truth. This is a gap omengrep can fill.

**What academic benchmarks miss:** They evaluate models, not systems. They don't measure indexing speed, index size, or query latency. CoIR is the state of the art for correctness but has no performance component.

**Ripgrep's methodology is the template for performance:** Pinned corpus, warmup, 10 runs, publish raw data, provide reproducible runner.

**ANN-Benchmarks is the template for the quality/speed tradeoff:** Recall vs. QPS plot is the canonical way to show where a system sits.

---

## References

- ColGrep/LateOn-Code blog: https://www.lighton.ai/lighton-blogs/lateon-code-colgrep-lighton
- ColGrep GitHub (NextPlaid): https://github.com/lightonai/next-plaid
- CoIR paper (ACL 2025): https://arxiv.org/html/2407.02883v3
- CoIR GitHub: https://github.com/CoIR-team/coir
- CodeSearchNet paper: https://arxiv.org/pdf/1909.09436
- CoSQA+ paper: https://arxiv.org/html/2406.11589v7
- ripgrep benchmark: https://burntsushi.net/ripgrep/
- ANN-Benchmarks: https://ann-benchmarks.com/
- MTEB v2 (Oct 2025): https://huggingface.co/blog/isaacchung/mteb-v2
- Cursor indexing blog: https://cursor.com/blog/secure-codebase-indexing
- Zoekt (Sourcegraph): https://sourcegraph.com/github.com/sourcegraph/zoekt
