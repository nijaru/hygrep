"""Test CLI module."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

import contextlib

from hygrep import cli


def test_exit_codes():
    """Test grep-compatible exit codes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello(): pass\n")

        # Build index first
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        # Test match (exit 0)
        sys.argv = ["hygrep", "-q", "hello", tmpdir]
        try:
            cli.main()
            raise AssertionError("Should have called sys.exit")
        except SystemExit as e:
            assert e.code == 0, f"Expected exit 0 on match, got {e.code}"

        # Test no match (exit 1) - use threshold to force no results
        sys.argv = ["hygrep", "-q", "--threshold", "0.99", "xyznonexistentzyx", tmpdir]
        try:
            cli.main()
            raise AssertionError("Should have called sys.exit")
        except SystemExit as e:
            assert e.code == 1, f"Expected exit 1 on no match, got {e.code}"

        # Test error (exit 2)
        sys.argv = ["hygrep", "-q", "test", "/nonexistent/path"]
        try:
            cli.main()
            raise AssertionError("Should have called sys.exit")
        except SystemExit as e:
            assert e.code == 2, f"Expected exit 2 on error, got {e.code}"

    print("Exit codes: PASS")


def test_json_output(capsys=None):
    """Test JSON output format."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "auth.py")
        with open(test_file, "w") as f:
            f.write("def login(): pass\n")

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        sys.argv = ["hygrep", "--json", "-q", "login", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        out = stdout.getvalue()
        results = json.loads(out)
        assert isinstance(results, list)
        assert len(results) > 0
        assert "file" in results[0]
        assert "type" in results[0]
        assert "name" in results[0]

    print("JSON output: PASS")


def test_exclude_patterns():
    """Test --exclude pattern filtering."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("def main(): pass\n")
        with open(os.path.join(tmpdir, "test_main.py"), "w") as f:
            f.write("def test_main(): pass\n")

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        # Without exclude
        sys.argv = ["hygrep", "--json", "-q", "main", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()
        results = json.loads(stdout.getvalue())
        assert len(results) >= 2, f"Expected >= 2 results, got {len(results)}"

        # With exclude
        sys.argv = ["hygrep", "--json", "-q", "--exclude", "test_*", "main", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()
        results = json.loads(stdout.getvalue())
        # Should have fewer results after exclusion
        for r in results:
            assert "test_main" not in r["file"], f"test_main should be excluded: {r['file']}"

    print("Exclude patterns: PASS")


def test_type_filter():
    """Test -t/--type file type filtering."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "code.py"), "w") as f:
            f.write("def hello(): pass\n")
        with open(os.path.join(tmpdir, "code.js"), "w") as f:
            f.write("function hello() {}\n")

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        sys.argv = ["hygrep", "--json", "-q", "-t", "py", "hello", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        results = json.loads(stdout.getvalue())
        assert len(results) >= 1, f"Expected >= 1 Python result, got {len(results)}"
        for r in results:
            assert r["file"].endswith(".py"), f"Expected .py file, got {r['file']}"

    print("Type filter: PASS")


def test_help():
    """Test --help flag."""
    import io
    from contextlib import redirect_stdout

    sys.argv = ["hygrep", "--help"]
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        try:
            cli.main()
        except SystemExit as e:
            assert e.code == 0

    out = stdout.getvalue()
    assert "hygrep" in out.lower()
    print("Help flag: PASS")


def test_files_only():
    """Test -l/--files-only option."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "a.py"), "w") as f:
            f.write("def hello(): pass\ndef world(): pass\n")
        with open(os.path.join(tmpdir, "b.py"), "w") as f:
            f.write("def hello(): pass\n")

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        sys.argv = ["hygrep", "-l", "-q", "hello", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        out = stdout.getvalue().strip()
        lines = [line for line in out.split("\n") if line]  # Filter empty lines
        # Should have unique files only
        assert len(lines) == len(set(lines)), "Files should be unique"
        assert len(lines) >= 1, f"Should have at least one file, got: {out!r}"
        expected_files = {"a.py", "b.py"}
        for line in lines:
            assert line in expected_files, f"Unexpected file '{line}' in output"

    print("Files only: PASS")


def test_compact_json():
    """Test --compact option for JSON without content."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello(): pass\n")

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        sys.argv = ["hygrep", "--json", "--compact", "-q", "hello", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        results = json.loads(stdout.getvalue())
        assert len(results) >= 1
        # Compact should NOT have content
        assert "content" not in results[0], "Compact JSON should not have content"
        # But should have other fields
        assert "file" in results[0]
        assert "line" in results[0]

    print("Compact JSON: PASS")


def test_semantic_mode():
    """Test default semantic search mode (builds index automatically)."""
    import io
    import shutil
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "auth.py")
        with open(test_file, "w") as f:
            f.write("def login(user, password):\n    # Authenticate user\n    return True\n")

        # Remove any existing index
        index_dir = os.path.join(tmpdir, ".hhg")
        if os.path.exists(index_dir):
            shutil.rmtree(index_dir)

        # Build index first (required for semantic search)
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with contextlib.suppress(SystemExit):
            cli.main()

        assert os.path.exists(index_dir), "Index should be created by build"

        # Semantic search (default mode)
        sys.argv = ["hygrep", "-q", "--json", "authentication", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        out = stdout.getvalue()
        results = json.loads(out)
        assert len(results) >= 1, "Should find at least 1 result"
        assert results[0]["name"] == "login", f"Expected 'login', got '{results[0]['name']}'"

    print("Semantic mode: PASS")


def test_status_command():
    """Test 'hhg status' command."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        # No index yet
        sys.argv = ["hygrep", "status", tmpdir]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), contextlib.suppress(SystemExit):
            cli.main()

        out = stdout.getvalue() + stderr.getvalue()
        assert "No index" in out or "not indexed" in out.lower() or "0" in out

        # Create a file and index it
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def foo(): pass\n")

        # Build index explicitly
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with redirect_stdout(io.StringIO()), contextlib.suppress(SystemExit):
            cli.main()

        # Now check status
        sys.argv = ["hygrep", "status", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        out = stdout.getvalue()
        # Should show some indexed content
        assert "1" in out or "block" in out.lower() or "file" in out.lower()

    print("Status command: PASS")


def test_build_command():
    """Test 'hhg build' command."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello(): pass\n")

        index_dir = os.path.join(tmpdir, ".hhg")
        assert not os.path.exists(index_dir), "Index should not exist yet"

        # Build index
        sys.argv = ["hygrep", "-q", "build", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        # Index should exist now
        assert os.path.exists(index_dir), "Index should exist after build"

    print("Build command: PASS")


def test_clean_command():
    """Test 'hhg clean' command."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file and build index
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello(): pass\n")

        sys.argv = ["hygrep", "-q", "build", tmpdir]
        with redirect_stdout(io.StringIO()), contextlib.suppress(SystemExit):
            cli.main()

        index_dir = os.path.join(tmpdir, ".hhg")
        assert os.path.exists(index_dir), "Index should exist before clean"

        # Clean
        sys.argv = ["hygrep", "clean", tmpdir]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        assert not os.path.exists(index_dir), "Index should be removed after clean"

    print("Clean command: PASS")


def test_list_command():
    """Test 'hhg list' command."""
    import io
    from contextlib import redirect_stderr, redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        # No indexes yet
        sys.argv = ["hygrep", "list", tmpdir]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), contextlib.suppress(SystemExit):
            cli.main()

        out = stdout.getvalue() + stderr.getvalue()
        assert "No indexes" in out or "no indexes" in out.lower()

        # Create subdirectory with index
        subdir = os.path.join(tmpdir, "sub")
        os.makedirs(subdir)
        test_file = os.path.join(subdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def foo(): pass\n")

        # Build index in subdir
        sys.argv = ["hygrep", "-q", "build", subdir]
        with redirect_stdout(io.StringIO()), contextlib.suppress(SystemExit):
            cli.main()

        # List should find the subdir index
        sys.argv = ["hygrep", "list", tmpdir]
        stdout = io.StringIO()
        with (
            redirect_stdout(stdout),
            redirect_stderr(io.StringIO()),
            contextlib.suppress(SystemExit),
        ):
            cli.main()

        out = stdout.getvalue()
        assert "sub" in out or ".hhg" in out, f"Should find subdir index, got: {out}"

    print("List command: PASS")


def test_clean_recursive():
    """Test 'hhg clean -r' recursive clean."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested structure with indexes
        subdir1 = os.path.join(tmpdir, "sub1")
        subdir2 = os.path.join(tmpdir, "sub2")
        os.makedirs(subdir1)
        os.makedirs(subdir2)

        for subdir in [subdir1, subdir2]:
            test_file = os.path.join(subdir, "test.py")
            with open(test_file, "w") as f:
                f.write("def foo(): pass\n")
            sys.argv = ["hygrep", "-q", "build", subdir]
            with redirect_stdout(io.StringIO()), contextlib.suppress(SystemExit):
                cli.main()

        # Verify indexes exist
        assert os.path.exists(os.path.join(subdir1, ".hhg"))
        assert os.path.exists(os.path.join(subdir2, ".hhg"))

        # Clean recursively
        sys.argv = ["hygrep", "clean", tmpdir, "-r"]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        # Both should be gone
        assert not os.path.exists(os.path.join(subdir1, ".hhg")), "sub1 index should be removed"
        assert not os.path.exists(os.path.join(subdir2, ".hhg")), "sub2 index should be removed"

    print("Clean recursive: PASS")


def test_model_command():
    """Test 'hhg model' command."""
    import io
    from contextlib import redirect_stdout

    # Just check that model status runs without error
    sys.argv = ["hygrep", "model"]
    stdout = io.StringIO()
    with redirect_stdout(stdout), contextlib.suppress(SystemExit):
        cli.main()

    out = stdout.getvalue()
    # Should show model status (installed or not)
    assert "model" in out.lower() or "nomic" in out.lower() or "✓" in out or "!" in out

    print("Model command: PASS")


if __name__ == "__main__":
    print("Running CLI tests...\n")
    test_exit_codes()
    test_json_output()
    test_exclude_patterns()
    test_type_filter()
    test_help()
    test_files_only()
    test_compact_json()
    test_semantic_mode()
    test_status_command()
    test_build_command()
    test_clean_command()
    test_list_command()
    test_clean_recursive()
    test_model_command()
    print("\nAll CLI tests passed!")
