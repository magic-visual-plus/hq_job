use std::net::TcpListener;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::Emitter;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;

use crate::config::AppConfig;
use crate::logger;

pub struct BackendState {
    pub port: u16,
    pub child_id: Option<u32>,
}

/// Find an available port. Try the preferred port first, fall back to OS-assigned.
pub fn find_available_port(preferred: u16) -> u16 {
    if TcpListener::bind(("127.0.0.1", preferred)).is_ok() {
        return preferred;
    }
    logger::info(&format!("Port {} is busy, finding alternative", preferred));
    // Let OS assign a port
    if let Ok(listener) = TcpListener::bind(("127.0.0.1", 0)) {
        if let Ok(addr) = listener.local_addr() {
            logger::info(&format!("Using alternative port {}", addr.port()));
            return addr.port();
        }
    }
    preferred // fallback, will fail at sidecar spawn
}

/// Start the Python backend sidecar.
pub fn start_backend(
    app: &tauri::AppHandle,
    config: &AppConfig,
    state: Arc<Mutex<BackendState>>,
) -> Result<(), String> {
    let port = find_available_port(config.server_port);

    // Update state with chosen port
    {
        let mut s = state.lock().unwrap();
        s.port = port;
    }

    logger::info(&format!("Creating sidecar command for port {}", port));

    let sidecar = app
        .shell()
        .sidecar("hq_job_server")
        .map_err(|e| {
            let msg = format!("Failed to create sidecar command: {}", e);
            logger::error(&msg);
            msg
        })?
        .env("AUTODL_TOKEN", &config.autodl_token)
        .env("API_TOKEN", &config.api_token)
        .env("SERVER_HOST", "127.0.0.1")
        .env("SERVER_PORT", port.to_string())
        .env("HQJOB_COS_PREFIX", &config.cos_prefix);

    let (mut rx, child) = sidecar
        .spawn()
        .map_err(|e| {
            let msg = format!("Failed to spawn sidecar: {}", e);
            logger::error(&msg);
            msg
        })?;

    let pid = child.pid();
    logger::info(&format!("Sidecar spawned with PID {}", pid));

    {
        let mut s = state.lock().unwrap();
        s.child_id = Some(pid);
    }

    // Capture sidecar stdout/stderr in background
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    let text = String::from_utf8_lossy(&line);
                    logger::info(&format!("[sidecar:out] {}", text.trim()));
                }
                CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line);
                    logger::info(&format!("[sidecar:err] {}", text.trim()));
                }
                CommandEvent::Terminated(payload) => {
                    logger::info(&format!("[sidecar] terminated: code={:?} signal={:?}", payload.code, payload.signal));
                    break;
                }
                CommandEvent::Error(err) => {
                    logger::error(&format!("[sidecar] error: {}", err));
                    break;
                }
                _ => {}
            }
        }
    });

    // Spawn health check in background
    let app_handle = app.clone();
    let check_port = port;
    tauri::async_runtime::spawn(async move {
        let url = format!("http://127.0.0.1:{}/health", check_port);
        logger::info(&format!("Starting health check: {}", url));

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(2))
            .build()
            .unwrap();

        for i in 0..60 {
            tokio::time::sleep(Duration::from_millis(500)).await;
            match client.get(&url).send().await {
                Ok(resp) if resp.status().is_success() => {
                    let nav_url = format!("http://127.0.0.1:{}/ui", check_port);
                    logger::info(&format!("Backend ready after {}ms, navigating to {}", (i + 1) * 500, nav_url));
                    let _ = app_handle.emit("backend-ready", nav_url);
                    return;
                }
                Ok(resp) => {
                    if i % 10 == 0 {
                        logger::info(&format!("Health check attempt {}: status {}", i + 1, resp.status()));
                    }
                }
                Err(e) => {
                    if i % 10 == 0 {
                        logger::info(&format!("Health check attempt {}: {}", i + 1, e));
                    }
                }
            }
        }
        logger::error("Backend startup timed out after 30s");
        let _ = app_handle.emit("backend-failed", "Backend startup timed out after 30s");
    });

    Ok(())
}

/// Kill the sidecar process.
pub fn stop_backend(state: Arc<Mutex<BackendState>>) {
    let child_id = {
        let mut s = state.lock().unwrap();
        s.child_id.take()
    };
    if let Some(pid) = child_id {
        logger::info(&format!("Stopping sidecar PID {}", pid));
        #[cfg(target_os = "windows")]
        {
            let _ = std::process::Command::new("taskkill")
                .args(["/F", "/T", "/PID", &pid.to_string()])
                .output();
        }
        #[cfg(not(target_os = "windows"))]
        {
            unsafe {
                libc::kill(pid as i32, libc::SIGTERM);
            }
        }
    }
}
