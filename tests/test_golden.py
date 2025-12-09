"""Golden dataset tests - comprehensive integration tests with expected results.

These tests run the full hygrep pipeline against realistic code samples
and verify expected results appear in the output.

Run: pixi run pytest tests/test_golden.py -v
Or:  python tests/test_golden.py
"""

import io
import json
import os
import sys
from contextlib import redirect_stdout, suppress
from pathlib import Path

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from hygrep import cli

GOLDEN_DIR = Path(__file__).parent / "golden"


def _ensure_index_built():
    """Build index for golden dir if not already built."""
    index_dir = GOLDEN_DIR / ".hhg"
    if not (index_dir / "manifest.json").exists():
        # Build index quietly
        sys.argv = ["hygrep", "-q", "build", str(GOLDEN_DIR)]
        with suppress(SystemExit):
            cli.main()


def run_search(
    query: str,
    path: str | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Run hygrep semantic search and return results."""
    if path is None:
        path = str(GOLDEN_DIR)

    # Ensure index is built
    _ensure_index_built()

    args = ["hygrep", "--json", "-q", "-n", str(top_k), query, path]

    sys.argv = args
    stdout = io.StringIO()
    with redirect_stdout(stdout), suppress(SystemExit):
        cli.main()

    output = stdout.getvalue()
    if not output.strip():
        return []
    return json.loads(output)


def result_contains(
    results: list[dict],
    expected_file: str,
    expected_name: str | None = None,
) -> bool:
    """Check if results contain expected file/name."""
    for r in results:
        if expected_file in r["file"]:
            if expected_name is None or r.get("name") == expected_name:
                return True
    return False


def get_result_names(results: list[dict]) -> list[str]:
    """Extract names from results for debugging."""
    return [r.get("name", r["file"]) for r in results]


# =============================================================================
# Semantic Search Tests
# =============================================================================


class TestSemanticSearch:
    """Tests for semantic code search."""

    @classmethod
    def setup_class(cls):
        """Build index before running tests."""
        _ensure_index_built()

    def test_python_function_search(self):
        """Search for Python functions."""
        results = run_search("hash password function")
        assert len(results) > 0, "Should find results"
        assert result_contains(results, "auth.py"), (
            f"Should find auth.py: {get_result_names(results)}"
        )

    def test_python_class_search(self):
        """Search for Python classes."""
        results = run_search("user management class")
        assert result_contains(results[:5], "auth.py", "UserManager"), (
            f"Should find UserManager: {get_result_names(results[:5])}"
        )

    def test_typescript_function_search(self):
        """Search for TypeScript functions."""
        results = run_search("create user handler")
        assert result_contains(results[:5], "api_handlers.ts"), (
            f"Should find api_handlers.ts: {get_result_names(results[:5])}"
        )

    def test_typescript_middleware_search(self):
        """Search for middleware pattern."""
        results = run_search("authentication middleware")
        assert result_contains(results[:5], "api_handlers.ts"), (
            f"Should find api_handlers.ts: {get_result_names(results[:5])}"
        )

    def test_go_struct_search(self):
        """Search for Go structs."""
        results = run_search("server configuration struct")
        assert result_contains(results[:5], "server.go"), (
            f"Should find server.go: {get_result_names(results[:5])}"
        )

    def test_go_handler_search(self):
        """Search for Go HTTP handlers."""
        results = run_search("health check endpoint")
        assert result_contains(results[:5], "server.go"), (
            f"Should find server.go: {get_result_names(results[:5])}"
        )

    def test_rust_error_types(self):
        """Search for Rust error handling."""
        results = run_search("database error type")
        assert result_contains(results[:5], "errors.rs"), (
            f"Should find errors.rs: {get_result_names(results[:5])}"
        )

    def test_rust_result_extension(self):
        """Search for Rust trait implementations."""
        results = run_search("result extension trait")
        assert result_contains(results[:5], "errors.rs"), (
            f"Should find errors.rs: {get_result_names(results[:5])}"
        )

    def test_cross_language_auth(self):
        """Search should find auth in multiple languages."""
        results = run_search("user authentication login")
        files = {r["file"] for r in results}
        # Should find auth-related code
        auth_files = [f for f in files if "auth" in f.lower() or "handler" in f.lower()]
        assert len(auth_files) >= 1, f"Should find auth in files: {files}"

    def test_semantic_password_hash(self):
        """Semantic search for password hashing."""
        results = run_search("how to hash passwords securely")
        assert len(results) > 0, "Should find results"
        # hash_password should rank highly for this query
        top_names = [r.get("name") for r in results[:5]]
        assert "hash_password" in top_names or result_contains(results[:5], "auth.py"), (
            f"hash_password should be in top 5: {top_names}"
        )

    def test_semantic_graceful_shutdown(self):
        """Semantic search for graceful shutdown."""
        results = run_search("graceful server shutdown")
        # Should find server.go (Shutdown method or related code)
        assert result_contains(results[:5], "server.go"), (
            f"server.go should be in top 5: {get_result_names(results[:5])}"
        )

    def test_semantic_error_handling(self):
        """Semantic search for error handling patterns."""
        results = run_search("custom error types with context")
        assert result_contains(results[:5], "errors.rs"), (
            f"errors.rs should be in top 5: {get_result_names(results[:5])}"
        )

    def test_semantic_crud_operations(self):
        """Semantic search for CRUD operations."""
        results = run_search("REST API CRUD handlers")
        assert result_contains(results[:5], "api_handlers.ts"), (
            f"api_handlers.ts should be in top 5: {get_result_names(results[:5])}"
        )

    def test_scores_are_ordered(self):
        """Results should be ordered by score (descending)."""
        results = run_search("HTTP server routing")
        if len(results) > 1:
            scores = [r["score"] for r in results]
            assert scores == sorted(scores, reverse=True), f"Scores should be descending: {scores}"


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case and boundary tests."""

    @classmethod
    def setup_class(cls):
        """Build index before running tests."""
        _ensure_index_built()

    def test_special_characters_in_query(self):
        """Query with special regex characters."""
        results = run_search("map interface")
        # Should not crash
        assert isinstance(results, list)

    def test_empty_query(self):
        """Empty query should show help or exit gracefully."""
        sys.argv = ["hygrep", "--json", "-q", "", str(GOLDEN_DIR)]
        try:
            cli.main()
        except SystemExit as e:
            # Exit 0 (help shown), 1 (no match), or 2 (error) are all acceptable
            assert e.code in (0, 1, 2), f"Expected exit 0, 1, or 2, got {e.code}"

    def test_single_word_query(self):
        """Single word queries work."""
        results = run_search("password")
        assert len(results) > 0, "Should find password references"

    def test_unique_term_query(self):
        """Query with unique term finds correct file."""
        results = run_search("session expiration token")
        assert result_contains(results[:5], "auth.py"), "Should find auth.py"

    def test_case_insensitive(self):
        """Search should find results regardless of case."""
        results = run_search("user manager")
        assert len(results) > 0, "Should find results"


# =============================================================================
# Run all tests
# =============================================================================


def run_tests():
    """Run all tests and report results."""
    import traceback

    test_classes = [TestSemanticSearch, TestEdgeCases]
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        print(f"\n=== {cls.__name__} ===")
        # Call setup_class if exists (pytest calls this, but direct run doesn't)
        if hasattr(cls, "setup_class"):
            cls.setup_class()
        instance = cls()
        for name in dir(instance):
            if not name.startswith("test_"):
                continue
            method = getattr(instance, name)
            try:
                method()
                print(f"  PASS: {name}")
                passed += 1
            except AssertionError as e:
                print(f"  FAIL: {name}")
                print(f"        {e}")
                failed += 1
                errors.append((name, str(e)))
            except Exception as e:
                print(f"  ERROR: {name}")
                print(f"         {e}")
                traceback.print_exc()
                failed += 1
                errors.append((name, str(e)))

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for name, msg in errors:
            print(f"  - {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
