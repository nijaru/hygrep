pub mod onnx;
pub mod tokenizer;

use anyhow::Result;
use ndarray::Array2;

/// Configuration for an embedding model.
pub struct ModelConfig {
    pub repo: &'static str,
    pub model_file: &'static str,
    pub tokenizer_file: &'static str,
    pub token_dim: usize,
    pub doc_max_length: usize,
    pub query_max_length: usize,
    pub version: &'static str,
    pub batch_size: usize,
}

/// Available models: (name, config) pairs.
pub const MODELS: &[(&str, ModelConfig)] = &[
    (
        "edge",
        ModelConfig {
            repo: "lightonai/LateOn-Code-edge",
            model_file: "model.onnx",
            tokenizer_file: "tokenizer.json",
            token_dim: 48,
            doc_max_length: 512,
            query_max_length: 256,
            version: "lateon-code-edge-v1",
            batch_size: 64,
        },
    ),
    (
        "full",
        ModelConfig {
            repo: "lightonai/LateOn-Code",
            model_file: "model.onnx",
            tokenizer_file: "tokenizer.json",
            token_dim: 128,
            doc_max_length: 512,
            query_max_length: 256,
            version: "lateon-code-v1",
            batch_size: 32,
        },
    ),
];

/// Default model (edge).
pub const EDGE_MODEL: &ModelConfig = &MODELS[0].1;

/// Backwards-compatible aliases for the default model.
pub const MODEL_REPO: &str = EDGE_MODEL.repo;
pub const MODEL_FILE: &str = EDGE_MODEL.model_file;
pub const TOKENIZER_FILE: &str = EDGE_MODEL.tokenizer_file;
pub const TOKEN_DIM: usize = EDGE_MODEL.token_dim;
pub const DOC_MAX_LENGTH: usize = EDGE_MODEL.doc_max_length;
pub const QUERY_MAX_LENGTH: usize = EDGE_MODEL.query_max_length;
pub const MODEL_VERSION: &str = EDGE_MODEL.version;
pub const BATCH_SIZE: usize = EDGE_MODEL.batch_size;

/// Resolve a model name to its config. Returns EDGE_MODEL for None.
pub fn resolve_model(name: Option<&str>) -> &'static ModelConfig {
    match name {
        Some(n) => MODELS
            .iter()
            .find(|(key, _)| *key == n)
            .map(|(_, config)| config)
            .unwrap_or(EDGE_MODEL),
        None => EDGE_MODEL,
    }
}

/// Resolve a model version string to its config.
pub fn resolve_model_by_version(version: &str) -> &'static ModelConfig {
    MODELS
        .iter()
        .find(|(_, config)| config.version == version)
        .map(|(_, config)| config)
        .unwrap_or(EDGE_MODEL)
}

/// Embedding output: variable-length token embeddings per document.
/// Each document produces (num_tokens, TOKEN_DIM) embeddings.
pub struct TokenEmbeddings {
    /// One entry per document: each is (num_tokens, token_dim).
    pub embeddings: Vec<Array2<f32>>,
}

/// Trait for multi-vector embedding backends.
pub trait Embedder: Send + Sync {
    /// Embed documents, returning per-token embeddings for each.
    fn embed_documents(&self, texts: &[&str]) -> Result<TokenEmbeddings>;

    /// Embed a query, returning token embeddings.
    fn embed_query(&self, text: &str) -> Result<Array2<f32>>;
}

/// Create the default embedder (edge model).
pub fn create_embedder() -> Result<Box<dyn Embedder>> {
    create_embedder_with_model(EDGE_MODEL)
}

/// Create an embedder for a specific model config.
pub fn create_embedder_with_model(model: &'static ModelConfig) -> Result<Box<dyn Embedder>> {
    Ok(Box::new(onnx::OnnxEmbedder::new_with_config(model)?))
}
