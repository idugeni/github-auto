use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Account {
    pub username: String,
    pub password: String,
    pub email: String,
    #[serde(default)]
    pub email_password: String,
    pub status: String,
    #[serde(default)]
    pub recovery_codes: Vec<String>,
    #[serde(default)]
    pub provider: String,
    #[serde(default)]
    pub proxy: String,
    #[serde(default)]
    pub error: String,
    pub created_at: String,
    #[serde(default)]
    pub verified_at: Option<String>,
    #[serde(default)]
    pub metadata: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Status {
    pub total: usize,
    pub created: usize,
    pub verified: usize,
    pub failed: usize,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StatusResponse {
    pub total: usize,
    pub created: usize,
    pub verified: usize,
    pub failed: usize,
    #[serde(default)]
    pub accounts: Vec<Account>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProxyEntry {
    pub url: String,
    #[serde(default)]
    pub country_code: String,
    #[serde(default)]
    pub country_name: String,
    pub healthy: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LogEntry {
    #[serde(default)]
    pub timestamp: String,
    #[serde(default)]
    pub level: String,
    #[serde(default)]
    pub message: String,
    #[serde(default)]
    pub module: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub email_provider: String,
    pub browser_headless: bool,
    #[serde(default)]
    pub proxy_url: String,
    pub delay_base: f64,
    pub delay_jitter: f64,
    #[serde(default)]
    pub password: String,
}

fn run_python_command(args: &[&str]) -> Result<String, String> {
    let output = Command::new("python")
        .arg("cli.py")
        .args(args)
        .current_dir(std::env::current_dir().unwrap().join(".."))
        .output()
        .map_err(|e| format!("Failed to run Python: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
async fn get_accounts() -> Result<Vec<Account>, String> {
    let output = tokio::task::spawn_blocking(|| run_python_command(&["status", "--json"]))
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| e.to_string())?;

    let response: StatusResponse = serde_json::from_str(&output)
        .map_err(|e| format!("Parse error: {}", e))?;
    Ok(response.accounts)
}

#[tauri::command]
async fn get_status() -> Result<Status, String> {
    let output = tokio::task::spawn_blocking(|| run_python_command(&["status", "--json"]))
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| e.to_string())?;

    let response: StatusResponse = serde_json::from_str(&output)
        .map_err(|e| format!("Parse error: {}", e))?;
    Ok(Status {
        total: response.total,
        created: response.created,
        verified: response.verified,
        failed: response.failed,
    })
}

#[tauri::command]
async fn register_accounts(count: usize) -> Result<String, String> {
    let count_str = count.to_string();
    tokio::task::spawn_blocking(move || run_python_command(&["register", "-n", &count_str]))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn export_accounts(format: String, path: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || run_python_command(&["export", "-f", &format, "-o", &path]))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn get_config() -> Result<AppConfig, String> {
    let output = tokio::task::spawn_blocking(|| run_python_command(&["config", "--json"]))
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| e.to_string())?;

    let config: AppConfig = serde_json::from_str(&output)
        .map_err(|e| format!("Parse error: {}", e))?;
    Ok(config)
}

#[tauri::command]
async fn update_config(key: String, value: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || run_python_command(&["config-set", &key, &value]))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn get_proxies() -> Result<Vec<ProxyEntry>, String> {
    let output = tokio::task::spawn_blocking(|| run_python_command(&["proxy", "list", "--json"]))
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| e.to_string())?;

    let proxies: Vec<ProxyEntry> = serde_json::from_str(&output)
        .map_err(|e| format!("Parse error: {}", e))?;
    Ok(proxies)
}

#[tauri::command]
async fn add_proxy(url: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || run_python_command(&["proxy", "add", &url]))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn remove_proxy(url: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || run_python_command(&["proxy", "remove", &url]))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn test_proxy(url: String) -> Result<String, String> {
    tokio::task::spawn_blocking(move || run_python_command(&["proxy", "test", &url]))
        .await
        .map_err(|e| e.to_string())?
}

#[tauri::command]
async fn get_logs(lines: Option<usize>) -> Result<Vec<LogEntry>, String> {
    let n = lines.unwrap_or(100).to_string();
    let output = tokio::task::spawn_blocking(move || run_python_command(&["logs", "-n", &n, "--json"]))
        .await
        .map_err(|e| e.to_string())?
        .map_err(|e| e.to_string())?;

    let logs: Vec<LogEntry> = serde_json::from_str(&output)
        .map_err(|e| format!("Parse error: {}", e))?;
    Ok(logs)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            get_accounts,
            get_status,
            register_accounts,
            export_accounts,
            get_config,
            update_config,
            get_proxies,
            add_proxy,
            remove_proxy,
            test_proxy,
            get_logs,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
