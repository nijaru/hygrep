"""Integration tests for model management commands.

These tests hit the network and modify the cache.
Run manually: python tests/test_model_integration.py
Not included in default test suite.
"""

import io
import os
import sys
from contextlib import redirect_stdout, suppress

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from hygrep import cli


def test_model_status():
    """Test 'hygrep model' shows status."""
    print("=== Testing model status ===\n")

    sys.argv = ["hygrep", "model"]
    stdout = io.StringIO()
    with redirect_stdout(stdout), suppress(SystemExit):
        cli.main()

    out = stdout.getvalue()
    assert "embedder" in out.lower(), f"Expected embedder info in output: {out}"
    print(f"   Output: {out.strip()}")
    print("   Model status: PASS")


def test_model_install():
    """Test 'hygrep model install' downloads model."""
    print("\n=== Testing model install ===\n")

    print("Running 'hygrep model install'...")
    sys.argv = ["hygrep", "model", "install"]
    stdout = io.StringIO()
    with redirect_stdout(stdout), suppress(SystemExit):
        cli.main()

    out = stdout.getvalue()
    print(f"   Output: {out.strip()}")

    # Verify model is installed
    sys.argv = ["hygrep", "model"]
    stdout = io.StringIO()
    with redirect_stdout(stdout), suppress(SystemExit):
        cli.main()

    out = stdout.getvalue()
    assert "installed" in out.lower() or "✓" in out, f"Expected installed status: {out}"
    print("   Model install: PASS")


def test_search_with_model():
    """Test search works after model is installed."""
    import tempfile

    print("\n=== Testing search with model ===\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "auth.py")
        with open(test_file, "w") as f:
            f.write("def login(username, password):\n    return True\n")

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with suppress(SystemExit):
            cli.main()

        # Search
        sys.argv = ["hygrep", "--json", "-q", "authentication", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), suppress(SystemExit):
            cli.main()

        import json

        results = json.loads(stdout.getvalue())
        assert len(results) >= 1, f"Expected results, got: {results}"
        print(f"   Search returned {len(results)} result(s)")

    print("   Search with model: PASS")


if __name__ == "__main__":
    test_model_status()
    test_model_install()
    test_search_with_model()
    print("\n=== All integration tests passed! ===")
