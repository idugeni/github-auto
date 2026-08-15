import {
  Minus,
  Square,
  X,
  PanelLeftClose,
  PanelLeft,
  Sun,
  Moon,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  title: string;
  subtitle?: string;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  isDark?: boolean;
  onToggleTheme?: () => void;
}

export function Header({
  title,
  subtitle,
  collapsed,
  onToggleCollapse,
  isDark,
  onToggleTheme,
}: HeaderProps) {
  return (
    <header className="titlebar flex items-center justify-between h-10 px-3 select-none">
      {/* Left: drag region + toggle */}
      <div className="flex items-center gap-2" data-tauri-drag-region>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onToggleCollapse}
        >
          {collapsed ? (
            <PanelLeft className="w-4 h-4" />
          ) : (
            <PanelLeftClose className="w-4 h-4" />
          )}
        </Button>
        <div className="flex flex-col" data-tauri-drag-region>
          <span className="text-xs font-medium leading-none" data-tauri-drag-region>
            {title}
          </span>
          {subtitle && (
            <span className="text-[10px] text-muted-foreground leading-none mt-0.5" data-tauri-drag-region>
              {subtitle}
            </span>
          )}
        </div>
      </div>

      {/* Right: theme + window controls */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onToggleTheme}
        >
          {isDark ? (
            <Sun className="w-3.5 h-3.5" />
          ) : (
            <Moon className="w-3.5 h-3.5" />
          )}
        </Button>

        <div className="flex items-center ml-2">
          <button className="flex items-center justify-center w-11 h-10 hover:bg-accent transition-colors">
            <Minus className="w-4 h-4" />
          </button>
          <button className="flex items-center justify-center w-11 h-10 hover:bg-accent transition-colors">
            <Square className="w-3 h-3" />
          </button>
          <button className="flex items-center justify-center w-11 h-10 hover:bg-destructive hover:text-destructive-foreground transition-colors rounded-tr-lg">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
