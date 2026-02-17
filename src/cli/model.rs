use anyhow::Result;
use hf_hub::api::sync::Api;

use crate::embedder::{self, ModelConfig, MODELS};

pub fn status() -> Result<()> {
    let api = Api::new()?;

    for (name, config) in MODELS {
        let repo = api.model(config.repo.to_string());
        let installed =
            repo.get(config.model_file).is_ok() && repo.get(config.tokenizer_file).is_ok();
        let marker = if installed {
            "installed"
        } else {
            "not installed"
        };
        println!("  {name:<8} {:<36} ({marker})", config.repo);
    }

    Ok(())
}

pub fn install(model_name: Option<&str>) -> Result<()> {
    let config = embedder::resolve_model(model_name);
    install_model(config)
}

fn install_model(config: &ModelConfig) -> Result<()> {
    let api = Api::new()?;
    let repo = api.model(config.repo.to_string());

    println!("Downloading {}...", config.repo);

    for filename in [config.model_file, config.tokenizer_file] {
        match repo.get(filename) {
            Ok(path) => {
                println!("  {filename} -> {}", path.display());
            }
            Err(e) => {
                eprintln!("Failed to download {filename}: {e}");
                eprintln!("Check network connection and try again");
                std::process::exit(crate::types::EXIT_ERROR);
            }
        }
    }

    println!("Model installed: {}", config.repo);
    Ok(())
}
