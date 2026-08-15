import {
  LayoutDashboard,
  Users,
  UserPlus,
  Globe,
  Mail,
  ScrollText,
  Download,
  Settings,
  Github,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "accounts", label: "Accounts", icon: Users },
  { id: "register", label: "Register", icon: UserPlus },
  { id: "proxies", label: "Proxies", icon: Globe },
  { id: "email", label: "Email", icon: Mail },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "export", label: "Export", icon: Download },
];

const bottomItems = [
  { id: "settings", label: "Settings", icon: Settings },
];

export function Sidebar({
  activePage,
  onNavigate,
  collapsed = false,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "sidebar-glass flex flex-col h-full transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-4 h-14 shrink-0">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10">
          <Github className="w-5 h-5 text-primary" />
        </div>
        {!collapsed && (
          <span className="font-semibold text-sm tracking-tight">GitHub Auto</span>
        )}
      </div>

      <Separator className="opacity-50" />

      {/* Main nav */}
      <nav className="flex-1 px-2 py-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "flex items-center gap-3 w-full rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      <Separator className="opacity-50" />

      {/* Bottom nav */}
      <div className="px-2 py-3 space-y-1">
        {bottomItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                "flex items-center gap-3 w-full rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </div>

      {/* Version stamp */}
      {!collapsed && (
        <div className="px-4 py-2 text-[10px] text-muted-foreground/50">
          v0.1.0
        </div>
      )}
    </aside>
  );
}
