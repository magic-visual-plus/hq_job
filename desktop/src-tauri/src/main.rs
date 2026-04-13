// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod logger;
mod sidecar;

use std::sync::{Arc, Mutex};

use sidecar::BackendState;

fn main() {
    logger::init();
    logger::info("HQ Job Desktop starting...");

    let backend_state = Arc::new(Mutex::new(BackendState {
        port: 9090,
        child_id: None,
    }));

    let state_for_exit = backend_state.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .manage(backend_state.clone())
        .invoke_handler(tauri::generate_handler![
            commands::get_config,
            commands::save_config_cmd,
            commands::get_server_url,
            commands::restart_backend,
            commands::open_settings,
        ])
        .setup(move |app| {
            logger::info("Tauri setup starting...");
            // If config exists, start backend immediately
            match config::load_config() {
                Some(cfg) => {
                    logger::info(&format!(
                        "Config found, starting backend on port {}",
                        cfg.server_port
                    ));
                    if let Err(e) = sidecar::start_backend(app.handle(), &cfg, backend_state.clone()) {
                        logger::error(&format!("Failed to start backend: {}", e));
                    }
                }
                None => {
                    logger::info("No config found, will show settings page");
                }
            }
            Ok(())
        })
        .on_window_event(move |_window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                logger::info("Window destroyed, stopping backend");
                sidecar::stop_backend(state_for_exit.clone());
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
