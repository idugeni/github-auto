import { invoke } from "@tauri-apps/api/core";

// Type definitions
export interface Account {
  username: string;
  password: string;
  email: string;
  email_password: string;
  status: "pending" | "created" | "verified" | "failed";
  recovery_codes: string[];
  provider: string;
  proxy: string;
  error: string;
  created_at: string;
  verified_at: string | null;
  metadata: Record<string, unknown>;
}

export interface Status {
  total: number;
  created: number;
  verified: number;
  failed: number;
}

export interface ProxyEntry {
  url: string;
  country_code: string;
  country_name: string;
  healthy: boolean;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  module: string;
}

export interface AppConfig {
  email_provider: string;
  browser_headless: boolean;
  proxy_url: string;
  delay_base: number;
  delay_jitter: number;
  password: string;
}

// IPC functions
export async function getAccounts(): Promise<Account[]> {
  return invoke<Account[]>("get_accounts");
}

export async function getStatus(): Promise<Status> {
  return invoke<Status>("get_status");
}

export async function registerAccounts(count: number): Promise<string> {
  return invoke<string>("register_accounts", { count });
}

export async function exportAccounts(
  format: string,
  path: string
): Promise<string> {
  return invoke<string>("export_accounts", { format, path });
}

export async function getConfig(): Promise<AppConfig> {
  return invoke<AppConfig>("get_config");
}

export async function updateConfig(
  key: string,
  value: string
): Promise<string> {
  return invoke<string>("update_config", { key, value });
}

export async function getProxies(): Promise<ProxyEntry[]> {
  return invoke<ProxyEntry[]>("get_proxies");
}

export async function addProxy(url: string): Promise<string> {
  return invoke<string>("add_proxy", { url });
}

export async function removeProxy(url: string): Promise<string> {
  return invoke<string>("remove_proxy", { url });
}

export async function testProxy(url: string): Promise<string> {
  return invoke<string>("test_proxy", { url });
}

export async function getLogs(lines?: number): Promise<LogEntry[]> {
  return invoke<LogEntry[]>("get_logs", { lines: lines ?? 100 });
}
