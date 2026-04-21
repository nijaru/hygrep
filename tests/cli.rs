#[allow(deprecated)]
use assert_cmd::Command;
use predicates::prelude::*;
use std::path::PathBuf;
use tempfile::TempDir;

fn json_files(stdout: &[u8]) -> Vec<String> {
    let v: serde_json::Value = serde_json::from_slice(stdout).unwrap_or(serde_json::json!([]));
    v.as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|r| r["file"].as_str().map(String::from))
        .collect()
}

fn fixtures_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/golden")
}

#[allow(deprecated)]
fn og() -> Command {
    Command::cargo_bin("og").unwrap()
}

/// Build an index in a temp directory by copying fixtures, return the temp dir.
fn build_fixture_index() -> TempDir {
    let tmp = TempDir::new().unwrap();
    let fixtures = fixtures_dir();

    // Copy fixture files to temp dir
    for entry in std::fs::read_dir(&fixtures).unwrap() {
        let entry = entry.unwrap();
        if entry.file_type().unwrap().is_file() {
            let dest = tmp.path().join(entry.file_name());
            std::fs::copy(entry.path(), &dest).unwrap();
        }
    }

    // Build index
    og().args(["build", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stderr(predicate::str::contains("Indexed"));

    tmp
}

#[test]
fn build_creates_index() {
    let tmp = build_fixture_index();
    assert!(tmp.path().join(".og/manifest.json").exists());
}

#[test]
fn status_shows_files() {
    let tmp = build_fixture_index();

    og().args(["status", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stdout(predicate::str::contains("files"))
        .stdout(predicate::str::contains("blocks"));
}

#[test]
fn search_finds_results() {
    let tmp = build_fixture_index();

    og().args(["error handling", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stdout(predicate::str::contains("errors.rs"));
}

#[test]
fn search_authentication() {
    let tmp = build_fixture_index();

    og().args(["authentication", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stdout(predicate::str::contains("auth.py"));
}

#[test]
fn search_gibberish_succeeds() {
    let tmp = build_fixture_index();

    // Semantic search (MaxSim) always returns candidates, even for gibberish.
    // Just verify the search completes and returns valid JSON.
    let output = og()
        .args([
            "--json",
            "zzzznonexistentqueryzzzz",
            tmp.path().to_str().unwrap(),
            "-n",
            "1",
        ])
        .assert()
        .success();

    let stdout = String::from_utf8(output.get_output().stdout.clone()).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    assert!(parsed.is_array());
}

#[test]
fn search_json_output() {
    let tmp = build_fixture_index();

    let output = og()
        .args(["--json", "error", tmp.path().to_str().unwrap(), "-n", "2"])
        .assert()
        .success();

    let stdout = String::from_utf8(output.get_output().stdout.clone()).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    assert!(parsed.is_array());
    assert!(!parsed.as_array().unwrap().is_empty());

    let first = &parsed[0];
    assert!(first.get("file").is_some());
    assert!(first.get("type").is_some());
    assert!(first.get("name").is_some());
    assert!(first.get("line").is_some());
    assert!(first.get("score").is_some());
}

#[test]
fn search_files_only() {
    let tmp = build_fixture_index();

    og().args(["-l", "authentication", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stdout(predicate::str::contains("auth.py"));
}

#[test]
fn search_type_filter() {
    let tmp = build_fixture_index();

    // Filter to .py files only — use "password" which is unique to auth.py
    let output = og()
        .args(["-t", "py", "password", tmp.path().to_str().unwrap()])
        .assert()
        .success();

    let stdout = String::from_utf8(output.get_output().stdout.clone()).unwrap();
    assert!(stdout.contains("auth.py"));
    assert!(!stdout.contains("errors.rs"));
}

#[test]
fn search_limit_results() {
    let tmp = build_fixture_index();

    let output = og()
        .args([
            "--json",
            "-n",
            "1",
            "function",
            tmp.path().to_str().unwrap(),
        ])
        .assert()
        .success();

    let stdout = String::from_utf8(output.get_output().stdout.clone()).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    assert_eq!(parsed.as_array().unwrap().len(), 1);
}

#[test]
fn clean_removes_index() {
    let tmp = build_fixture_index();
    assert!(tmp.path().join(".og").exists());

    og().args(["clean", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stdout(predicate::str::contains("Deleted"));

    assert!(!tmp.path().join(".og").exists());
}

#[test]
fn no_index_exits_2() {
    let tmp = TempDir::new().unwrap();
    std::fs::write(tmp.path().join("test.rs"), "fn main() {}").unwrap();

    og().args(["query", tmp.path().to_str().unwrap()])
        .assert()
        .code(2)
        .stderr(predicate::str::contains("No index found"));
}

#[test]
fn build_force_rebuilds() {
    let tmp = build_fixture_index();

    og().args(["build", "--force", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stderr(predicate::str::contains("Indexed"));
}

#[test]
fn incremental_update() {
    let tmp = build_fixture_index();

    // Add a new file
    std::fs::write(
        tmp.path().join("new_file.py"),
        "def hello_world():\n    print('hello')\n",
    )
    .unwrap();

    // Search should auto-update
    og().args(["hello", tmp.path().to_str().unwrap()])
        .assert()
        .success()
        .stderr(predicate::str::contains("Updating"));
}

#[test]
fn camel_case_query_matches() {
    let tmp = build_fixture_index();

    // The fixtures have camelCase identifiers (api_handlers.ts)
    // Query with split terms should match
    og().args(["user manager", tmp.path().to_str().unwrap()])
        .assert()
        .success();
}

// Regression: starts_with("src/cli") matched src/cli_utils — fix uses exact+slash guard.
#[test]
fn scope_filter_excludes_sibling_directory() {
    let tmp = TempDir::new().unwrap();
    std::fs::create_dir_all(tmp.path().join("src/cli")).unwrap();
    std::fs::create_dir_all(tmp.path().join("src/cli_utils")).unwrap();

    std::fs::write(
        tmp.path().join("src/cli/mod.rs"),
        "pub fn run_dispatch() {}\npub fn execute_command() {}\n",
    )
    .unwrap();
    // Unique term "quuxhelper" only in cli_utils — BM25 will surface it unscoped
    std::fs::write(
        tmp.path().join("src/cli_utils/helper.rs"),
        "pub fn quuxhelper_format() {}\npub fn quuxhelper_parse() {}\n",
    )
    .unwrap();

    og().args(["build", tmp.path().to_str().unwrap()])
        .assert()
        .success();

    // Unscoped: cli_utils file must be findable (proves it's indexed)
    let out = og()
        .args([
            "--json",
            "-n",
            "10",
            "quuxhelper",
            tmp.path().to_str().unwrap(),
        ])
        .output()
        .unwrap();
    let files = json_files(&out.stdout);
    assert!(
        files.iter().any(|f| f.contains("cli_utils")),
        "unscoped search must find cli_utils/helper.rs; got: {files:?}"
    );

    // Scoped to src/cli: cli_utils must be excluded
    let cli_path = tmp.path().join("src/cli");
    let out = og()
        .args([
            "--json",
            "-n",
            "10",
            "quuxhelper",
            cli_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    let files = json_files(&out.stdout);
    assert!(
        !files.iter().any(|f| f.contains("cli_utils")),
        "scoped search must exclude src/cli_utils; got: {files:?}"
    );
}

// Regression: all chunks from a long markdown section got the same ID — only the last survived.
#[test]
fn markdown_long_section_indexes_all_chunks() {
    let tmp = TempDir::new().unwrap();
    // ~2000 chars → ~500 tokens → 2 chunks at CHUNK_SIZE=400
    let long_content = "detailed explanation of the semantic indexing pipeline. ".repeat(40)
        + &"additional content about vector embeddings and retrieval. ".repeat(20);
    let md = format!("# Architecture\n\n{long_content}\n");
    std::fs::write(tmp.path().join("README.md"), &md).unwrap();

    let out = og()
        .args(["build", tmp.path().to_str().unwrap()])
        .output()
        .unwrap();
    let stderr = String::from_utf8_lossy(&out.stderr);
    // Extract block count from "Indexed N blocks from M files"
    let blocks: usize = stderr
        .split_whitespace()
        .skip_while(|w| *w != "Indexed")
        .nth(1)
        .and_then(|n| n.parse().ok())
        .unwrap_or(0);
    assert!(
        blocks >= 2,
        "long markdown section must produce ≥2 indexed chunks; got {blocks}"
    );
}

// Regression: similar search showed score as "-40099% similar" for negative MaxSim scores.
#[test]
fn similar_search_shows_raw_score_not_percentage() {
    let tmp = build_fixture_index();
    // File ref requires the path to exist; use absolute path to the fixture copy
    let file_ref = format!("{}#AppError", tmp.path().join("errors.rs").display());

    let out = og()
        .args([&file_ref, tmp.path().to_str().unwrap()])
        .output()
        .unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains("score:"),
        "similar search must show 'score:'; got: {stdout}"
    );
    assert!(
        !stdout.contains("% similar"),
        "similar search must not show '% similar'; got: {stdout}"
    );
}
