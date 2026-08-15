import { useState } from "react";
import { Shell } from "@/components/layout/shell";
import { DashboardPage } from "@/features/dashboard/page";
import { AccountsPage } from "@/features/accounts/page";
import { RegisterPage } from "@/features/register/page";
import { ProxiesPage } from "@/features/proxy/page";
import { EmailPage } from "@/features/email/page";
import { LogsPage } from "@/features/logs/page";
import { ExportPage } from "@/features/export/page";
import { SettingsPage } from "@/features/settings/page";

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  const renderPage = () => {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage onNavigate={setActivePage} />;
      case "accounts":
        return <AccountsPage />;
      case "register":
        return <RegisterPage />;
      case "proxies":
        return <ProxiesPage />;
      case "email":
        return <EmailPage />;
      case "logs":
        return <LogsPage />;
      case "export":
        return <ExportPage />;
      case "settings":
        return <SettingsPage />;
      default:
        return <DashboardPage onNavigate={setActivePage} />;
    }
  };

  return (
    <Shell activePage={activePage} onNavigate={setActivePage}>
      {renderPage()}
    </Shell>
  );
}

export default App;
