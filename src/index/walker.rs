use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use anyhow::Result;
use ignore::WalkBuilder;

/// Maximum file size to index (1MB).
const MAX_FILE_SIZE: u64 = 1_000_000;

/// Binary file extensions to skip.
const BINARY_EXTENSIONS: &[&str] = &[
    // Compiled/object files
    ".pyc",
    ".pyo",
    ".o",
    ".so",
    ".dylib",
    ".dll",
    ".bin",
    ".exe",
    ".a",
    ".lib",
    // Archives
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".jar",
    ".war",
    ".whl",
    // Documents/media
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    // Images
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".bmp",
    ".tiff",
    // Audio/video
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".mkv",
    // Data files
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pkl",
    ".npy",
    ".npz",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
    // Lock files
    ".lock",
];

/// Metadata for a scanned file: (file_size, mtime_secs).
pub type FileMetadata = (u64, u64);

/// Check if a file path should be skipped during scanning.
fn should_skip(path: &Path) -> bool {
    if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
        if name.starts_with('.') || name.ends_with("-lock.json") {
            return true;
        }
    }
    if let Some(ext) = path.extension().and_then(|e| e.to_str()) {
        let ext_lower = format!(".{}", ext.to_lowercase());
        if BINARY_EXTENSIONS.contains(&ext_lower.as_str()) {
            return true;
        }
    }
    false
}

/// Build a directory walker with standard filtering options.
fn build_walker(root: &Path) -> ignore::Walk {
    WalkBuilder::new(root)
        .hidden(true)
        .git_ignore(true)
        .git_global(true)
        .git_exclude(true)
        .follow_links(false)
        .max_filesize(Some(MAX_FILE_SIZE))
        .build()
}

/// Scan directory tree for file metadata only (no content reads).
/// Returns path -> (file_size, mtime_secs) for each eligible file.
pub fn scan_metadata(root: &Path) -> Result<HashMap<PathBuf, FileMetadata>> {
    let mut results = HashMap::new();

    for entry in build_walker(root) {
        let entry = match entry {
            Ok(e) => e,
            Err(_) => continue,
        };

        if entry.file_type().is_none_or(|ft| !ft.is_file()) {
            continue;
        }

        let path = entry.path();
        if should_skip(path) {
            continue;
        }

        if let Ok(meta) = std::fs::metadata(path) {
            let size = meta.len();
            let mtime = meta
                .modified()
                .unwrap_or(SystemTime::UNIX_EPOCH)
                .duration_since(SystemTime::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0);
            results.insert(path.to_path_buf(), (size, mtime));
        }
    }

    Ok(results)
}

/// Get mtime for a single file path.
pub fn file_mtime(path: &Path) -> u64 {
    std::fs::metadata(path)
        .and_then(|m| m.modified())
        .unwrap_or(SystemTime::UNIX_EPOCH)
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Scan directory tree for text files, returning path -> (content, mtime).
/// mtime is captured before reading content so it's never newer than what was read.
pub fn scan(root: &Path) -> Result<HashMap<PathBuf, (String, u64)>> {
    let mut results = HashMap::new();

    for entry in build_walker(root) {
        let entry = match entry {
            Ok(e) => e,
            Err(_) => continue,
        };

        if entry.file_type().is_none_or(|ft| !ft.is_file()) {
            continue;
        }

        let path = entry.path();
        if should_skip(path) {
            continue;
        }

        // Stat before read so mtime is never newer than the content we index
        let mtime = file_mtime(path);

        let raw = match std::fs::read(path) {
            Ok(data) => data,
            Err(_) => continue,
        };

        // Binary detection: null byte in first 8192 bytes
        let check_len = raw.len().min(8192);
        if raw[..check_len].contains(&0) {
            continue;
        }

        let content = match String::from_utf8(raw) {
            Ok(s) => s,
            Err(_) => continue,
        };

        results.insert(path.to_path_buf(), (content, mtime));
    }

    Ok(results)
}
