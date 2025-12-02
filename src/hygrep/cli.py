"""hygrep CLI - Hybrid grep with neural reranking."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def is_regex_pattern(query: str) -> bool:
    """Check if query contains regex metacharacters."""
    return any(c in query for c in "*()[]\\|+?^$")


def main():
    parser = argparse.ArgumentParser(
        prog="hygrep",
        description="Hybrid search: grep speed + LLM intelligence",
    )
    parser.add_argument("query", nargs="?", help="Search query (natural language or regex)")
    parser.add_argument("path", nargs="?", default=".", help="Directory to search (default: .)")
    parser.add_argument("-n", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--json", action="store_true", help="Output JSON for agents")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    parser.add_argument("-v", "--version", action="version", version=f"hygrep {__version__}")
    parser.add_argument("--fast", action="store_true", help="Skip neural reranking (instant grep)")
    parser.add_argument(
        "-t", "--type", dest="file_types", help="Filter by file type (e.g., py,js,ts)"
    )
    parser.add_argument(
        "--max-candidates", type=int, default=100, help="Max candidates to rerank (default: 100)"
    )

    args = parser.parse_args()

    if not args.query:
        if args.json:
            print("[]")
        else:
            parser.print_help()
        return

    root = Path(args.path)
    if not root.exists():
        if args.json:
            print(json.dumps({"error": f"Path does not exist: {args.path}"}))
        else:
            print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(1)

    if not root.is_dir():
        if args.json:
            print(json.dumps({"error": f"Path is not a directory: {args.path}"}))
        else:
            print(f"Error: Path is not a directory: {args.path}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet and not args.json:
        print(f"Searching for '{args.query}' in {args.path}", file=sys.stderr)

    # Query expansion: "login auth" -> "login|auth" for better recall
    scanner_query = args.query
    if " " in args.query and not is_regex_pattern(args.query):
        scanner_query = args.query.replace(" ", "|")

    # 1. Recall phase - Mojo scanner
    try:
        from ._scanner import scan
    except ImportError:
        print("Error: _scanner.so not found. Run: mojo build src/scanner/_scanner.mojo --emit shared-lib -o src/hygrep/_scanner.so", file=sys.stderr)
        sys.exit(1)

    file_contents = scan(str(root), scanner_query)

    # Filter by file type if specified
    if args.file_types:
        type_map = {
            "py": [".py"],
            "js": [".js", ".jsx"],
            "ts": [".ts", ".tsx"],
            "rust": [".rs"],
            "go": [".go"],
            "java": [".java"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh"],
            "rb": [".rb"],
            "php": [".php"],
            "sh": [".sh", ".bash"],
            "md": [".md", ".markdown"],
            "json": [".json"],
            "yaml": [".yaml", ".yml"],
            "toml": [".toml"],
        }
        allowed_exts = set()
        for t in args.file_types.split(","):
            t = t.strip().lower()
            if t in type_map:
                allowed_exts.update(type_map[t])
            else:
                allowed_exts.add(f".{t}")
        file_contents = {
            k: v for k, v in file_contents.items() if any(k.endswith(ext) for ext in allowed_exts)
        }

    if not args.quiet and not args.json:
        print(f"Found {len(file_contents)} candidates", file=sys.stderr)

    if len(file_contents) == 0:
        if args.json:
            print("[]")
        return

    # 2. Rerank phase (or fast mode)
    if args.fast:
        # Fast mode: skip neural reranking, just return grep matches with extraction
        from .extractor import ContextExtractor

        extractor = ContextExtractor()
        results = []
        for path, content in list(file_contents.items())[: args.n]:
            blocks = extractor.extract(path, args.query, content=content)
            for block in blocks:
                results.append({
                    "file": path,
                    "type": block["type"],
                    "name": block["name"],
                    "start_line": block["start_line"],
                    "content": block["content"],
                    "score": 0.0,  # No score in fast mode
                })
        results = results[: args.n]
    else:
        if not args.quiet and not args.json:
            print("Reranking...", file=sys.stderr)

        from .reranker import Reranker

        reranker = Reranker()
        results = reranker.search(
            args.query, file_contents, top_k=args.n, max_candidates=args.max_candidates
        )

    if args.json:
        print(json.dumps(results))
        return

    if not results:
        print("No relevant results.", file=sys.stderr)
        return

    # Output results
    for item in results:
        file = item["file"]
        name = item["name"]
        score = item["score"]
        kind = item["type"]
        start_line = item["start_line"]
        if args.fast:
            print(f"{file}:{start_line} [{kind}] {name}")
        else:
            print(f"{file}:{start_line} [{kind}] {name} ({score})")


if __name__ == "__main__":
    main()
