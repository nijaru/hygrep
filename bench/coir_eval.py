#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "datasets",
#   "tqdm",
#   "numpy",
# ]
# ///
"""CoIR Benchmark Evaluator for omengrep.

This script evaluates omengrep against the CoIR (Code Information Retrieval)
benchmark (arXiv:2407.02883) or a local repository.

Usage:
    uv run bench/coir_eval.py --dataset CoIR-Retrieval/cosqa
    uv run bench/coir_eval.py --repo ~/github/rtk-ai/rtk

Metrics: nDCG@10, Recall@1/5/10, MRR@10.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from datasets import load_dataset
from tqdm import tqdm


def dcg(rel, k):
    """Compute Discounted Cumulative Gain."""
    rel = np.asarray(rel, dtype=float)[:k]
    if rel.size:
        return np.sum(rel / np.log2(np.arange(2, rel.size + 2)))
    return 0.0


def ndcg(rel, gold_rel, k):
    """Compute Normalized Discounted Cumulative Gain."""
    idcg = dcg(sorted(gold_rel, reverse=True), k)
    if not idcg:
        return 0.0
    return dcg(rel, k) / idcg


def evaluate_metrics(qrels, results, k=10):
    """Compute nDCG@k, Recall@k, and MRR@k."""
    ndcg_scores = []
    recall_at_1 = []
    recall_at_5 = []
    recall_at_k = []
    mrr_scores = []

    for qid, gold_matches in qrels.items():
        # gold_matches is a dict mapping doc_id -> score
        top_results = results.get(qid, [])

        # Binary relevance for MRR/Recall
        binary_rel = [1 if r["id"] in gold_matches else 0 for r in top_results]

        # Scores for nDCG
        scores = [gold_matches.get(r["id"], 0) for r in top_results]

        gold_scores = list(gold_matches.values())

        ndcg_scores.append(ndcg(scores, gold_scores, k))

        # Recall@n
        recall_at_1.append(1.0 if any(binary_rel[:1]) else 0.0)
        recall_at_5.append(1.0 if any(binary_rel[:5]) else 0.0)
        recall_at_k.append(1.0 if any(binary_rel[:k]) else 0.0)

        # MRR
        mrr = 0.0
        for i, rel in enumerate(binary_rel[:k], 1):
            if rel:
                mrr = 1.0 / i
                break
        mrr_scores.append(mrr)

    return {
        "ndcg@10": np.mean(ndcg_scores),
        "recall@1": np.mean(recall_at_1),
        "recall@5": np.mean(recall_at_5),
        f"recall@{k}": np.mean(recall_at_k),
        "mrr@10": np.mean(mrr_scores),
    }


def run_og_search(og_bin, query, target_dir, k=10):
    """Run og search and return parsed JSON results."""
    cmd = [og_bin, query, str(target_dir), "--json", "-n", str(k)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode == 1:
        return []
    if r.returncode != 0:
        raise RuntimeError(f"og search failed for query {query!r}: {r.stderr.strip()}")
    if not r.stdout.strip():
        return []

    # og output format: list of { file, block, score, ... }. For CoIR datasets,
    # the file stem is the corpus ID because corpus files are named <doc_id>.py.
    data = json.loads(r.stdout)
    return [
        {"id": os.path.basename(item["file"]).split(".")[0], "score": item["score"]}
        for item in data
    ]


def build_index(og_bin, target_dir, force=True):
    """Build og index for the target directory."""
    print(f"Building index for {target_dir}...")
    cmd = [og_bin, "build", str(target_dir), "--quiet"]
    if force:
        cmd.append("--force")
    r = subprocess.run(cmd, check=False)
    if r.returncode != 0:
        print(f"Build failed with exit code {r.returncode}", file=sys.stderr)
        sys.exit(1)


def eval_coir(
    dataset_name,
    og_bin,
    work_dir,
    k=10,
    limit_queries=None,
    limit_corpus=None,
    force_build=True,
):
    """Evaluate og on a CoIR dataset."""
    print(f"Loading CoIR dataset: {dataset_name}...")
    corpus = load_dataset(dataset_name, "corpus", split="corpus")
    queries = load_dataset(dataset_name, "queries", split="queries")

    # Load qrels from all splits that follow the standard BEIR format
    qrels = defaultdict(dict)
    splits_to_check = ["train", "test", "valid"]
    for split in splits_to_check:
        try:
            qrels_raw = load_dataset(dataset_name, "default", split=split)
            for qrel in qrels_raw:
                qrels[qrel["query-id"]][qrel["corpus-id"]] = qrel["score"]
        except Exception:
            # Not all datasets have all splits
            pass

    # Filter queries that have qrels before optionally shrinking the corpus.
    relevant_queries = [q for q in queries if q["_id"] in qrels]
    if limit_queries:
        rng = random.Random(42)
        relevant_queries = rng.sample(
            relevant_queries, min(limit_queries, len(relevant_queries))
        )

    eval_qrels = {q["_id"]: qrels[q["_id"]] for q in relevant_queries}

    selected_doc_ids = None
    if limit_corpus:
        rng = random.Random(42)
        gold_ids = {doc_id for matches in eval_qrels.values() for doc_id in matches}
        all_ids = [doc["_id"] for doc in corpus]
        candidates = [doc_id for doc_id in all_ids if doc_id not in gold_ids]
        sample_size = max(0, limit_corpus - len(gold_ids))
        selected_doc_ids = gold_ids | set(
            rng.sample(candidates, min(sample_size, len(candidates)))
        )

    corpus_dir = work_dir / dataset_name.split("/")[-1] / "corpus"
    if limit_corpus and force_build and corpus_dir.exists():
        shutil.rmtree(corpus_dir)
    corpus_dir.mkdir(parents=True, exist_ok=True)

    docs_to_write = [
        doc
        for doc in corpus
        if selected_doc_ids is None or doc["_id"] in selected_doc_ids
    ]
    print(f"Corpus size: {len(docs_to_write)} docs")

    for doc in tqdm(docs_to_write, desc="Writing corpus"):
        doc_id = doc["_id"]
        # Use .py extension so tree-sitter picks it up correctly
        file_path = corpus_dir / f"{doc_id}.py"
        if not file_path.exists():
            file_path.write_text(doc["text"], encoding="utf-8")

    build_index(og_bin, corpus_dir, force=force_build)

    print(f"Evaluating {len(relevant_queries)} queries...")
    all_results = {}
    for q in tqdm(relevant_queries, desc="Querying"):
        qid = q["_id"]
        res = run_og_search(og_bin, q["text"], corpus_dir, k)
        all_results[qid] = res

        # Debug first query
        if qid == relevant_queries[0]["_id"]:
            print(f"\nDebug Query {qid}: '{q['text']}'")
            print(f"  Gold IDs: {list(qrels[qid].keys())}")
            print(f"  Top IDs:  {[r['id'] for r in res]}")

    metrics = evaluate_metrics(eval_qrels, all_results, k)
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", help="CoIR dataset name (e.g., CoIR-Retrieval/cosqa)"
    )
    parser.add_argument("--repo", help="Path to local repository to evaluate")
    parser.add_argument("--og-bin", default="og", help="Path to og binary")
    parser.add_argument(
        "--work-dir",
        default="bench/coir_work",
        help="Working directory for corpus files",
    )
    parser.add_argument(
        "--limit-queries",
        type=int,
        help="Limit number of queries for faster evaluation",
    )
    parser.add_argument(
        "--limit-corpus",
        type=int,
        help="Limit corpus docs for smoke tests while preserving sampled gold docs",
    )
    parser.add_argument("--k", type=int, default=10, help="Recall/nDCG cutoff")
    parser.add_argument(
        "--reuse-index",
        action="store_true",
        help="Reuse an existing og index instead of forcing a clean rebuild",
    )

    args = parser.parse_args()
    work_dir = Path(args.work_dir)
    og_bin = args.og_bin

    if not args.dataset and not args.repo:
        parser.print_help()
        sys.exit(1)

    if args.dataset:
        metrics = eval_coir(
            args.dataset,
            og_bin,
            work_dir,
            args.k,
            args.limit_queries,
            args.limit_corpus,
            force_build=not args.reuse_index,
        )

        print("\n" + "=" * 40)
        print(f"  CoIR Evaluation: {args.dataset}")
        print("=" * 40)
        for name, score in metrics.items():
            print(f"  {name:<12}: {score:.4f}")
        print("=" * 40)

    elif args.repo:
        print("Local repo evaluation is not yet implemented (Phase 2).")
        # For Phase 2, we would:
        # 1. build_index(repo)
        # 2. Extract function docstrings/names using og outline --json
        # 3. Use those as queries, matching against the file/block they came from.
        sys.exit(0)


if __name__ == "__main__":
    main()
