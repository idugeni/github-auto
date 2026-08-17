import { create } from "zustand";
import {
  getStatus,
  getAccounts,
  getProxies,
  getConfig,
  getLogs,
} from "./tauri-ipc";
import type { Account, Status, ProxyEntry, AppConfig, LogEntry } from "./tauri-ipc";

interface AppState {
  // Data
  status: Status;
  accounts: Account[];
  proxies: ProxyEntry[];
  config: AppConfig | null;
  logs: LogEntry[];

  // UI state
  loading: boolean;
  error: string | null;

  // Actions
  refreshStatus: () => Promise<void>;
  refreshAccounts: () => Promise<void>;
  refreshProxies: () => Promise<void>;
  refreshConfig: () => Promise<void>;
  refreshLogs: (lines?: number) => Promise<void>;
  refreshAll: () => Promise<void>;
  setError: (error: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  status: { total: 0, created: 0, verified: 0, failed: 0 },
  accounts: [],
  proxies: [],
  config: null,
  logs: [],
  loading: false,
  error: null,

  refreshStatus: async () => {
    try {
      const status = await getStatus();
      set({ status });
    } catch (e) {
      console.error("Failed to refresh status:", e);
    }
  },

  refreshAccounts: async () => {
    try {
      const accounts = await getAccounts();
      set({ accounts });
    } catch (e) {
      console.error("Failed to refresh accounts:", e);
    }
  },

  refreshProxies: async () => {
    try {
      const proxies = await getProxies();
      set({ proxies });
    } catch (e) {
      console.error("Failed to refresh proxies:", e);
    }
  },

  refreshConfig: async () => {
    try {
      const config = await getConfig();
      set({ config });
    } catch (e) {
      console.error("Failed to refresh config:", e);
    }
  },

  refreshLogs: async (lines = 200) => {
    try {
      const logs = await getLogs(lines);
      set({ logs });
    } catch (e) {
      console.error("Failed to refresh logs:", e);
    }
  },

  refreshAll: async () => {
    set({ loading: true });
    try {
      const [status, accounts, proxies, config, logs] = await Promise.all([
        getStatus(),
        getAccounts(),
        getProxies(),
        getConfig(),
        getLogs(200),
      ]);
      set({ status, accounts, proxies, config, logs, error: null });
    } catch (e) {
      set({ error: e instanceof Error ? e.message : "Failed to load data" });
    } finally {
      set({ loading: false });
    }
  },

  setError: (error) => set({ error }),
}));
