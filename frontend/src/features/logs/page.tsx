import { useEffect, useState, useRef } from "react";
import { Search, Trash2, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { getLogs } from "@/lib/tauri-ipc";
import type { LogEntry } from "@/lib/tauri-ipc";

const levelColors: Record<string, string> = {
  INFO: "text-emerald-500",
  WARNING: "text-amber-500",
  ERROR: "text-red-500",
  DEBUG: "text-muted-foreground",
};

export function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadLogs();
    const interval = setInterval(loadLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  async function loadLogs() {
    try {
      const data = await getLogs(200);
      setLogs(data);
    } catch (e) {
      console.error("Failed to load logs:", e);
    } finally {
      setLoading(false);
    }
  }

  const filtered = logs.filter(
    (log) =>
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.module.toLowerCase().includes(filter.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Logs</h2>
          <Badge variant="success" className="animate-pulse">
            Live
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Filter logs..."
              className="pl-9 w-64"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon" onClick={loadLogs}>
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Log viewer */}
      <Card className="glass-card flex-1 min-h-0">
        <ScrollArea ref={scrollRef} className="h-full">
          <div className="p-4 font-mono text-xs space-y-1">
            {filtered.map((log, i) => (
              <div key={i} className="flex gap-3 hover:bg-accent/30 rounded px-2 py-0.5">
                <span className="text-muted-foreground shrink-0">{log.timestamp}</span>
                <span className={`shrink-0 w-16 ${levelColors[log.level] || "text-foreground"}`}>
                  {log.level}
                </span>
                <span className="text-muted-foreground shrink-0 w-20">[{log.module}]</span>
                <span className="text-foreground">{log.message}</span>
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No logs found
              </div>
            )}
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}
