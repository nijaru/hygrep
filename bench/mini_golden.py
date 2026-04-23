#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple

QUERIES: List[Tuple[str, str]] = [
    ("How do I update a user's role or details in the REST API?", "api_handlers.ts"),
    ("Validate and decode JSON Web Tokens", "auth.py"),
    ("Application specific error definitions and mapping", "errors.rs"),
    ("Connect to PostgreSQL and manage the connection pool", "database.rs"),
    ("Process background jobs from the queue", "workers.rs"),
]

def search(og: str, query: str, corpus_dir: Path, k: int) -> List[Dict]:
    r = subprocess.run(
        [og, query, str(corpus_dir), "--json", "-n", str(k)],
        capture_output=True,
        text=True,
    )
    if r.returncode == 2 or not r.stdout.strip():
        return []
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return []

def evaluate(og: str, queries: List[Tuple[str, str]], corpus_dir: Path, k: int) -> Dict:
    reciprocal_ranks: List[float] = []
    hits: Dict[int, int] = {1: 0, 3: 0, 5: 0}

    print(f"Running {len(queries)} queries...")
    for query, gold_file in queries:
        results = search(og, query, corpus_dir, k)

        rank = None
        for i, r in enumerate(results, 1):
            if Path(r.get("file", "")).name == gold_file:
                rank = i
                break

        rr = 1.0 / rank if rank is not None else 0.0
        reciprocal_ranks.append(rr)
        if rank is not None:
            for cutoff in hits:
                if rank <= cutoff:
                    hits[cutoff] += 1
                    
        print(f"Q: {query[:50]:<50} | Gold: {gold_file:<15} | Rank: {rank if rank else 'N/A'}")

    n = len(queries)
    return {
        "n_queries": n,
        "mrr": round(sum(reciprocal_ranks) / n, 4),
        "recall@1": round(hits[1] / n, 4),
        "recall@3": round(hits[3] / n, 4),
        "recall@5": round(hits[5] / n, 4),
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Mini-Golden Benchmark for omengrep")
    parser.add_argument("--corpus-dir", default="bench/golden")
    parser.add_argument("--og-bin", default="og")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    og = args.og_bin
    k = args.k

    if not corpus_dir.exists():
        print(f"Corpus directory not found: {corpus_dir}")
        sys.exit(1)

    print(f"Building index for {corpus_dir}...")
    r = subprocess.run([og, "build", str(corpus_dir)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Build failed:\n{r.stderr}")
        sys.exit(1)

    metrics = evaluate(og, QUERIES, corpus_dir, k)

    print("\n" + "=" * 44)
    print("  omengrep Mini-Golden Benchmark")
    print("=" * 44)
    print(f"  MRR@{k:<6}: {metrics['mrr']:.4f}")
    print(f"  Recall@1 : {metrics['recall@1']:.4f}")
    print(f"  Recall@3 : {metrics['recall@3']:.4f}")
    print(f"  Recall@{k:<2}: {metrics[f'recall@{k}']:.4f}")
    print("=" * 44 + "\n")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
