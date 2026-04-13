use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct AppConfig {
    pub autodl_token: String,
    pub api_token: String,
    #[serde(default)]
    pub cos_prefix: String,
    #[serde(default = "default_port")]
    pub server_port: u16,
}

fn default_port() -> u16 {
    9090
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            autodl_token: String::new(),
            api_token: String::new(),
            cos_prefix: String::from("cos://autodl"),
            server_port: 9090,
        }
    }
}

fn config_dir() -> PathBuf {
    let base = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    base.join("hq-job-desktop")
}

fn config_path() -> PathBuf {
    config_dir().join("config.json")
}

pub fn load_config() -> Option<AppConfig> {
    let path = config_path();
    let data = fs::read_to_string(&path).ok()?;
    let cfg: AppConfig = serde_json::from_str(&data).ok()?;
    if cfg.autodl_token.is_empty() || cfg.api_token.is_empty() {
        return None;
    }
    Some(cfg)
}

pub fn save_config(config: &AppConfig) -> Result<(), String> {
    let dir = config_dir();
    fs::create_dir_all(&dir).map_err(|e| format!("Failed to create config dir: {}", e))?;
    let json =
        serde_json::to_string_pretty(config).map_err(|e| format!("Failed to serialize: {}", e))?;
    fs::write(config_path(), json).map_err(|e| format!("Failed to write config: {}", e))?;
    Ok(())
}
