import React, { useState } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";

interface ShellProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: "Dashboard", subtitle: "Overview and quick actions" },
  accounts: { title: "Accounts", subtitle: "Manage created accounts" },
  register: { title: "Register", subtitle: "Create new GitHub accounts" },
  proxies: { title: "Proxies", subtitle: "Proxy pool management" },
  email: { title: "Email", subtitle: "Email provider configuration" },
  logs: { title: "Logs", subtitle: "Real-time log viewer" },
  export: { title: "Export", subtitle: "Export accounts to file" },
  settings: { title: "Settings", subtitle: "Application configuration" },
};

export function Shell({ children, activePage, onNavigate }: ShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  const pageInfo = pageTitles[activePage] || {
    title: "GitHub Auto",
    subtitle: "",
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden rounded-lg border border-border/50 bg-background">
      {/* Sidebar */}
      <Sidebar
        activePage={activePage}
        onNavigate={onNavigate}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0">
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed(!collapsed)}
          isDark={isDark}
          onToggleTheme={toggleTheme}
        />

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
