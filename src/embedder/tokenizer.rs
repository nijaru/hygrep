use anyhow::{Context, Result};
use tokenizers::Tokenizer;

use super::{DOC_MAX_LENGTH, MODEL_REPO, QUERY_MAX_LENGTH, TOKENIZER_FILE};

/// Wrapper around HuggingFace tokenizer.
/// Pre-configured with truncation/padding to avoid cloning per batch.
pub struct TokenizerWrapper {
    doc_tokenizer: Tokenizer,
    query_tokenizer: Tokenizer,
}

impl TokenizerWrapper {
    pub fn new() -> Result<Self> {
        let tokenizer_path = download_tokenizer()?;
        let base = Tokenizer::from_file(&tokenizer_path).map_err(|e| anyhow::anyhow!("{e}"))?;

        let mut doc_tokenizer = base.clone();
        doc_tokenizer
            .with_truncation(Some(tokenizers::TruncationParams {
                max_length: DOC_MAX_LENGTH,
                ..Default::default()
            }))
            .map_err(|e| anyhow::anyhow!("{e}"))?;
        doc_tokenizer.with_padding(Some(tokenizers::PaddingParams::default()));

        let mut query_tokenizer = base;
        query_tokenizer
            .with_truncation(Some(tokenizers::TruncationParams {
                max_length: QUERY_MAX_LENGTH,
                ..Default::default()
            }))
            .map_err(|e| anyhow::anyhow!("{e}"))?;
        query_tokenizer.with_padding(Some(tokenizers::PaddingParams::default()));

        Ok(Self {
            doc_tokenizer,
            query_tokenizer,
        })
    }

    /// Encode texts for document embedding.
    pub fn encode_documents(&self, texts: &[&str]) -> Result<Vec<tokenizers::Encoding>> {
        let inputs: Vec<tokenizers::EncodeInput> = texts
            .iter()
            .map(|t| tokenizers::EncodeInput::Single((*t).into()))
            .collect();
        self.doc_tokenizer
            .encode_batch(inputs, true)
            .map_err(|e| anyhow::anyhow!("{e}"))
    }

    /// Encode a query (shorter max length).
    pub fn encode_query(&self, text: &str) -> Result<tokenizers::Encoding> {
        self.query_tokenizer
            .encode(text, true)
            .map_err(|e| anyhow::anyhow!("{e}"))
    }
}

fn download_tokenizer() -> Result<String> {
    let api = hf_hub::api::sync::Api::new().context("Failed to create HF Hub API")?;
    let repo = api.model(MODEL_REPO.to_string());
    let path = repo
        .get(TOKENIZER_FILE)
        .context("Failed to download tokenizer")?;
    Ok(path.to_string_lossy().into_owned())
}
