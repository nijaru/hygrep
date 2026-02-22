#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "datasets",
#   "tqdm",
# ]
# ///
"""CodeSearchNet quality benchmark for omengrep.

Corpus:  Nan-Do/code-search-net-python test partition, subsampled
Queries: docstrings as NL queries, sampled from corpus (seed=42)
Metrics: MRR@10, Recall@1/5/10

Default: 2000 corpus functions, 100 queries (~5 min).
Full run: --corpus-size 22091 --queries 500 (~100 min, subprocess overhead).

Usage:
    uv run bench/quality.py [options]

    --corpus-dir DIR    Where to write corpus files (default: bench/corpus)
    --og-bin PATH       Path to og binary (default: og)
    --corpus-size N     Functions to index (default: 2000; 22091 = full)
    --queries N         Queries to sample from corpus (default: 100)
    --k N               Recall cutoff, also MRR@k (default: 10)
    --skip-corpus       Skip writing corpus files (already written)
    --skip-build        Skip og build (index already built)

Run from the omengrep repo root.
"""

import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm


def write_corpus(examples: list[dict], corpus_dir: Path) -> None:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    for idx, ex in enumerate(tqdm(examples, desc="Writing corpus")):
        (corpus_dir / f"{idx:06d}.py").write_text(ex["code"], encoding="utf-8")


def build_index(og: str, corpus_dir: Path) -> None:
    print(f"Building index: {og} build {corpus_dir}")
    r = subprocess.run([og, "build", str(corpus_dir)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(1)
    if r.stdout.strip():
        print(r.stdout.strip())


def search(og: str, query: str, corpus_dir: Path, k: int) -> list[dict]:
    r = subprocess.run(
        [og, query, str(corpus_dir), "--json", "-n", str(k)],
        capture_output=True,
        text=True,
    )
    # exit 0 = results, 1 = no match, 2 = error
    if r.returncode == 2 or not r.stdout.strip():
        return []
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return []


def evaluate(og: str, queries: list[tuple[int, str]], corpus_dir: Path, k: int) -> dict:
    reciprocal_ranks: list[float] = []
    hits: dict[int, int] = {1: 0, 5: 0, k: 0}

    for idx, query in tqdm(queries, desc="Querying"):
        gold = f"{idx:06d}.py"
        results = search(og, query, corpus_dir, k)

        rank = None
        for i, r in enumerate(results, 1):
            # file is relative to corpus_dir root (strip_prefix applied by og)
            if os.path.basename(r.get("file", "")) == gold:
                rank = i
                break

        reciprocal_ranks.append(1.0 / rank if rank is not None else 0.0)
        if rank is not None:
            for cutoff in hits:
                if rank <= cutoff:
                    hits[cutoff] += 1

    n = len(queries)
    return {
        "n_queries": n,
        "mrr": round(sum(reciprocal_ranks) / n, 4),
        "recall@1": round(hits[1] / n, 4),
        "recall@5": round(hits[5] / n, 4),
        f"recall@{k}": round(hits[k] / n, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", default="bench/corpus")
    parser.add_argument("--og-bin", default="og")
    parser.add_argument("--corpus-size", type=int, default=2000)
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--skip-corpus", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    og = args.og_bin
    k = args.k

    print("Loading Nan-Do/code-search-net-python ...")
    ds = load_dataset("Nan-Do/code-search-net-python", split="train")
    test_ds = ds.filter(lambda x: x["partition"] == "test", desc="Filtering test")
    all_examples = list(test_ds)
    print(f"Test split: {len(all_examples)} functions total")

    # Subsample corpus (deterministic, seed=42)
    rng = random.Random(42)
    corpus_pool = [
        (i, ex)
        for i, ex in enumerate(all_examples)
        if ex.get("docstring", "").strip() and ex.get("code", "").strip()
    ]
    corpus_sample = rng.sample(corpus_pool, min(args.corpus_size, len(corpus_pool)))
    # Re-index 0..N so filenames are dense (gold matching stays consistent)
    examples = [(new_i, orig_i, ex) for new_i, (orig_i, ex) in enumerate(corpus_sample)]
    print(f"Corpus size: {len(examples)} functions (seed=42)")

    if not args.skip_corpus:
        corpus_dir.mkdir(parents=True, exist_ok=True)
        for new_i, _orig_i, ex in tqdm(examples, desc="Writing corpus"):
            (corpus_dir / f"{new_i:06d}.py").write_text(ex["code"], encoding="utf-8")
    else:
        print(f"Using existing corpus at {corpus_dir}")

    if not args.skip_build:
        build_index(og, corpus_dir)
    else:
        print("Skipping index build")

    # Sample queries from corpus (gold is always present in the index)
    queries = [
        (new_i, ex["docstring"].strip())
        for new_i, _orig_i, ex in rng.sample(examples, min(args.queries, len(examples)))
    ]
    print(f"Sampled {len(queries)} queries (seed=42)")

    metrics = evaluate(og, queries, corpus_dir, k)
    metrics["corpus_size"] = len(examples)

    print()
    print("=" * 44)
    print("  omengrep Quality Benchmark")
    print("=" * 44)
    print("  Dataset : Nan-Do/code-search-net-python")
    print(f"  Corpus  : {len(examples)} functions (test partition, seed=42)")
    print(f"  Queries : {metrics['n_queries']} (seed=42)")
    print()
    print(f"  MRR@{k:<6}: {metrics['mrr']:.4f}")
    print(f"  Recall@1 : {metrics['recall@1']:.4f}")
    print(f"  Recall@5 : {metrics['recall@5']:.4f}")
    print(f"  Recall@{k:<2}: {metrics[f'recall@{k}']:.4f}")
    print("=" * 44)
    print()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
