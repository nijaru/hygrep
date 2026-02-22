#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "datasets",
#   "tqdm",
# ]
# ///
"""CodeSearchNet quality benchmark for omengrep.

Corpus:  Nan-Do/code-search-net-python test partition (~22k functions)
Queries: docstrings as NL queries, 500 sampled (seed=42)
Metrics: MRR@10, Recall@1/5/10

Usage:
    uv run bench/quality.py [options]

    --corpus-dir DIR   Where to write corpus files (default: bench/corpus)
    --og-bin PATH      Path to og binary (default: og)
    --queries N        Number of queries to sample (default: 500)
    --k N              Recall cutoff, also MRR@k (default: 10)
    --skip-corpus      Skip writing corpus files (already written)
    --skip-build       Skip og build (index already built)

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
    parser.add_argument("--queries", type=int, default=500)
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
    examples = list(test_ds)
    print(f"Test split: {len(examples)} functions")

    valid = [
        (i, ex)
        for i, ex in enumerate(examples)
        if ex.get("docstring", "").strip() and ex.get("code", "").strip()
    ]
    print(f"Valid (non-empty docstring + code): {len(valid)}")

    if not args.skip_corpus:
        write_corpus(examples, corpus_dir)
    else:
        print(f"Using existing corpus at {corpus_dir}")

    if not args.skip_build:
        build_index(og, corpus_dir)
    else:
        print("Skipping index build")

    queries = [
        (i, ex["docstring"].strip())
        for i, ex in random.Random(42).sample(valid, min(args.queries, len(valid)))
    ]
    print(f"Sampled {len(queries)} queries (seed=42)")

    metrics = evaluate(og, queries, corpus_dir, k)

    print()
    print("=" * 44)
    print("  omengrep Quality Benchmark")
    print("=" * 44)
    print("  Dataset : Nan-Do/code-search-net-python")
    print(f"  Corpus  : {len(examples)} functions (test partition)")
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
