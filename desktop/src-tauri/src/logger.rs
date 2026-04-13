use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::OnceLock;

static LOG_PATH: OnceLock<PathBuf> = OnceLock::new();

fn log_dir() -> PathBuf {
    let base = dirs::data_local_dir().unwrap_or_else(|| PathBuf::from("."));
    base.join("hq-job-desktop").join("logs")
}

pub fn init() {
    let dir = log_dir();
    let _ = fs::create_dir_all(&dir);
    let path = dir.join("app.log");

    // Truncate if larger than 2MB
    if let Ok(meta) = fs::metadata(&path) {
        if meta.len() > 2 * 1024 * 1024 {
            let _ = fs::remove_file(&path);
        }
    }

    LOG_PATH.set(path).ok();
}

pub fn log(level: &str, msg: &str) {
    let Some(path) = LOG_PATH.get() else { return };
    let ts = chrono::Local::now().format("%Y-%m-%d %H:%M:%S%.3f");
    let line = format!("[{}] [{}] {}\n", ts, level, msg);

    // Also print to stderr for debug builds
    #[cfg(debug_assertions)]
    eprint!("{}", line);

    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = f.write_all(line.as_bytes());
    }
}

pub fn info(msg: &str) {
    log("INFO", msg);
}

pub fn error(msg: &str) {
    log("ERROR", msg);
}
