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

        # Test match (exit 0)
        sys.argv = ["hygrep", "hello", tmpdir, "-q", "--fast"]
        try:
            cli.main()
            raise AssertionError("Should have called sys.exit")
        except SystemExit as e:
            assert e.code == 0, f"Expected exit 0 on match, got {e.code}"

        # Test no match (exit 1)
        sys.argv = ["hygrep", "nonexistent_xyz", tmpdir, "-q", "--fast"]
        try:
            cli.main()
            raise AssertionError("Should have called sys.exit")
        except SystemExit as e:
            assert e.code == 1, f"Expected exit 1 on no match, got {e.code}"

        # Test error (exit 2)
        sys.argv = ["hygrep", "test", "/nonexistent/path", "-q"]
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

        sys.argv = ["hygrep", "login", tmpdir, "--json", "--fast", "-q"]
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

        # Without exclude
        sys.argv = ["hygrep", "main", tmpdir, "--json", "--fast", "-q"]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()
        results = json.loads(stdout.getvalue())
        assert len(results) >= 2, f"Expected >= 2 results, got {len(results)}"

        # With exclude
        sys.argv = ["hygrep", "main", tmpdir, "--json", "--fast", "-q", "--exclude", "test_*"]
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

        sys.argv = ["hygrep", "hello", tmpdir, "--json", "--fast", "-q", "-t", "py"]
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


def test_info_command():
    """Test 'hygrep info' command."""
    import io
    from contextlib import redirect_stdout

    sys.argv = ["hygrep", "info"]
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        try:
            cli.main()
        except SystemExit as e:
            assert e.code == 0, f"Expected exit 0, got {e.code}"

    out = stdout.getvalue()
    assert "hygrep" in out
    assert "Model:" in out or "Model" in out
    assert "Scanner:" in out or "scanner" in out.lower()

    print("Info command: PASS")


def test_model_command():
    """Test 'hygrep model' command."""
    import io
    from contextlib import redirect_stdout

    sys.argv = ["hygrep", "model", "status"]
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        try:
            cli.main()
        except SystemExit as e:
            # Exit 0 if installed, 1 if not
            assert e.code in (0, 1), f"Expected exit 0 or 1, got {e.code}"

    out = stdout.getvalue()
    assert "mixedbread-ai" in out or "Repository" in out

    print("Model command: PASS")


def test_fast_mode():
    """Test --fast mode (skip reranking)."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello(): pass\n")

        sys.argv = ["hygrep", "hello", tmpdir, "--fast", "--json", "-q"]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        results = json.loads(stdout.getvalue())
        assert len(results) >= 1
        # Fast mode should have score 0.0
        assert results[0]["score"] == 0.0

    print("Fast mode: PASS")


def test_files_only():
    """Test -l/--files-only option."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "a.py"), "w") as f:
            f.write("def hello(): pass\ndef world(): pass\n")
        with open(os.path.join(tmpdir, "b.py"), "w") as f:
            f.write("def hello(): pass\n")

        sys.argv = ["hygrep", "hello", tmpdir, "-l", "--fast", "-q", "--color", "never"]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        lines = stdout.getvalue().strip().split("\n")
        # Should have unique files only
        assert len(lines) == len(set(lines)), "Files should be unique"
        assert len(lines) >= 1, "Should have at least one file"
        for line in lines:
            assert line.endswith(".py"), f"Expected .py file, got {line}"

    print("Files only: PASS")


def test_compact_json():
    """Test --compact option for JSON without content."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello(): pass\n")

        sys.argv = ["hygrep", "hello", tmpdir, "--json", "--compact", "--fast", "-q"]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        results = json.loads(stdout.getvalue())
        assert len(results) >= 1
        # Compact should NOT have content
        assert "content" not in results[0], "Compact JSON should not have content"
        # But should have other fields
        assert "file" in results[0]
        assert "start_line" in results[0]
        assert "end_line" in results[0]

    print("Compact JSON: PASS")


def test_end_line_in_json():
    """Test that end_line is present in JSON output."""
    import io
    from contextlib import redirect_stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    pass\n    return True\n")

        sys.argv = ["hygrep", "hello", tmpdir, "--json", "--fast", "-q"]
        stdout = io.StringIO()
        with redirect_stdout(stdout), contextlib.suppress(SystemExit):
            cli.main()

        results = json.loads(stdout.getvalue())
        assert len(results) >= 1
        assert "start_line" in results[0], "Missing start_line"
        assert "end_line" in results[0], "Missing end_line"
        assert results[0]["end_line"] >= results[0]["start_line"], (
            "end_line should be >= start_line"
        )

    print("End line in JSON: PASS")


if __name__ == "__main__":
    print("Running CLI tests...\n")
    test_exit_codes()
    test_json_output()
    test_exclude_patterns()
    test_type_filter()
    test_help()
    test_info_command()
    test_model_command()
    test_fast_mode()
    test_files_only()
    test_compact_json()
    test_end_line_in_json()
    print("\nAll CLI tests passed!")
