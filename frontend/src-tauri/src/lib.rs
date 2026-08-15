use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::Manager;

#[derive(Debug, Serialize, Deserialize)]
pub struct Account {
    pub username: String,
    pub password: String,
    pub email: String,
    pub email_password: String,
    pub status: String,
    pub recovery_codes: Vec<String>,
    pub provider: String,
    pub proxy: String,
    pub error: String,
    pub created_at: String,
    pub verified_at: Option<String>,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Status {
    pub total: usize,
    pub created: usize,
    pub verified: usize,
    pub failed: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProxyEntry {
    pub url: String,
    pub country_code: String,
    pub country_name: String,
    pub healthy: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LogEntry {
    pub timestamp: String,
    pub level: String,
    pub message: String,
    pub module: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub email_provider: String,
    pub browser_driver: String,
    pub browser_headless: bool,
    pub proxy_url: String,
    pub delay_base: f64,
    pub delay_jitter: f64,
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
fn get_accounts() -> Result<Vec<Account>, String> {
    let output = run_python_command(&["status", "--json"])?;
    let accounts: Vec<Account> = serde_json::from_str(&output)
        .unwrap_or_default();
    Ok(accounts)
}

#[tauri::command]
fn get_status() -> Result<Status, String> {
    let output = run_python_command(&["status", "--json"])?;
    let status: Status = serde_json::from_str(&output)
        .unwrap_or(Status { total: 0, created: 0, verified: 0, failed: 0 });
    Ok(status)
}

#[tauri::command]
fn register_accounts(count: usize, _config: serde_json::Value) -> Result<String, String> {
    run_python_command(&["register", "-n", &count.to_string()])
}

#[tauri::command]
fn export_accounts(format: String, path: String) -> Result<usize, String> {
    let output = run_python_command(&["export", "-f", &format, "-o", &path])?;
    output.trim().parse::<usize>().map_err(|e| e.to_string())
}

#[tauri::command]
fn get_config() -> Result<AppConfig, String> {
    let output = run_python_command(&["config", "--json"])?;
    let config: AppConfig = serde_json::from_str(&output)
        .unwrap_or(AppConfig {
            email_provider: "lewattok".to_string(),
            browser_driver: "camoufox".to_string(),
            browser_headless: false,
            proxy_url: String::new(),
            delay_base: 8.0,
            delay_jitter: 2.0,
            password: "AutoGen2026!".to_string(),
        });
    Ok(config)
}

#[tauri::command]
fn update_config(config: AppConfig) -> Result<(), String> {
    let json = serde_json::to_string(&config).map_err(|e| e.to_string())?;
    run_python_command(&["config", "set", &json])?;
    Ok(())
}

#[tauri::command]
fn get_proxies() -> Result<Vec<ProxyEntry>, String> {
    let output = run_python_command(&["proxy", "list", "--json"])?;
    let proxies: Vec<ProxyEntry> = serde_json::from_str(&output)
        .unwrap_or_default();
    Ok(proxies)
}

#[tauri::command]
fn add_proxy(url: String) -> Result<(), String> {
    run_python_command(&["proxy", "add", &url])?;
    Ok(())
}

#[tauri::command]
fn remove_proxy(url: String) -> Result<(), String> {
    run_python_command(&["proxy", "remove", &url])?;
    Ok(())
}

#[tauri::command]
fn test_proxy(url: String) -> Result<bool, String> {
    let output = run_python_command(&["proxy", "test", &url])?;
    Ok(output.trim() == "ok")
}

#[tauri::command]
fn get_logs(lines: Option<usize>) -> Result<Vec<LogEntry>, String> {
    let n = lines.unwrap_or(100).to_string();
    let output = run_python_command(&["logs", "-n", &n, "--json"])?;
    let logs: Vec<LogEntry> = serde_json::from_str(&output)
        .unwrap_or_default();
    Ok(logs)
}

#[tauri::command]
fn start_registration(count: usize) -> Result<String, String> {
    run_python_command(&["register", "-n", &count.to_string()])
}

#[tauri::command]
fn stop_registration() -> Result<(), String> {
    // Signal Python process to stop
    Ok(())
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
            start_registration,
            stop_registration,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
