use std::sync::{Arc, Mutex};
use tauri::State;

use crate::config::{self, AppConfig};
use crate::logger;
use crate::sidecar::{self, BackendState};

#[tauri::command]
pub fn get_config() -> Option<AppConfig> {
    let cfg = config::load_config();
    logger::info(&format!("get_config called, result: {}", cfg.is_some()));
    cfg
}

#[tauri::command]
pub fn save_config_cmd(config: AppConfig) -> Result<(), String> {
    logger::info(&format!(
        "save_config_cmd called, token_len={}, api_len={}, port={}",
        config.autodl_token.len(),
        config.api_token.len(),
        config.server_port
    ));
    let result = config::save_config(&config);
    match &result {
        Ok(()) => logger::info("Config saved successfully"),
        Err(e) => logger::error(&format!("Config save failed: {}", e)),
    }
    result
}

#[tauri::command]
pub fn get_server_url(state: State<'_, Arc<Mutex<BackendState>>>) -> String {
    let s = state.lock().unwrap();
    let url = format!("http://127.0.0.1:{}", s.port);
    logger::info(&format!("get_server_url: {}", url));
    url
}

#[tauri::command]
pub fn restart_backend(
    app: tauri::AppHandle,
    state: State<'_, Arc<Mutex<BackendState>>>,
) -> Result<(), String> {
    logger::info("restart_backend called");
    // Stop existing
    sidecar::stop_backend(state.inner().clone());

    // Load fresh config
    let config = config::load_config().ok_or_else(|| {
        let msg = "No config found after save".to_string();
        logger::error(&msg);
        msg
    })?;

    // Start new backend
    sidecar::start_backend(&app, &config, state.inner().clone())
}

#[tauri::command]
pub fn open_settings(webview_window: tauri::WebviewWindow) -> Result<(), String> {
    logger::info("open_settings called");
    webview_window
        .eval("window.location.href = 'index.html';")
        .map_err(|e| e.to_string())
}
