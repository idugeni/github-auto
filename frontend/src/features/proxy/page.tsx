import { useEffect, useState } from "react";
import { Plus, Trash2, Globe, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { getProxies, addProxy, removeProxy } from "@/lib/tauri-ipc";
import type { ProxyEntry } from "@/lib/tauri-ipc";

export function ProxiesPage() {
  const [proxies, setProxies] = useState<ProxyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [newProxy, setNewProxy] = useState("");

  useEffect(() => {
    loadProxies();
  }, []);

  async function loadProxies() {
    try {
      const data = await getProxies();
      setProxies(data);
    } catch (e) {
      console.error("Failed to load proxies:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd() {
    if (!newProxy.trim()) return;
    try {
      await addProxy(newProxy);
      setNewProxy("");
      await loadProxies();
    } catch (e) {
      console.error("Failed to add proxy:", e);
    }
  }

  async function handleRemove(url: string) {
    try {
      await removeProxy(url);
      await loadProxies();
    } catch (e) {
      console.error("Failed to remove proxy:", e);
    }
  }

  const healthy = proxies.filter((p) => p.healthy).length;
  const unhealthy = proxies.length - healthy;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-3xl">
      {/* Add Proxy */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Add Proxy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="protocol://user:pass@host:port|Country"
              className="flex-1"
              value={newProxy}
              onChange={(e) => setNewProxy(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            />
            <Button onClick={handleAdd}>
              <Plus className="w-4 h-4 mr-1" />
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Proxy List */}
      <Card className="glass-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Proxy Pool</CardTitle>
          <div className="flex gap-2">
            <Badge variant="success">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              {healthy} Healthy
            </Badge>
            <Badge variant="destructive">
              <XCircle className="w-3 h-3 mr-1" />
              {unhealthy} Unhealthy
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {proxies.map((proxy) => (
              <div
                key={proxy.url}
                className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Globe className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <span className="font-mono text-sm">{proxy.url}</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      {proxy.country_code && (
                        <Badge variant="outline" className="text-[10px]">
                          {proxy.country_code}
                        </Badge>
                      )}
                      {proxy.healthy ? (
                        <Badge variant="success" className="text-[10px]">Healthy</Badge>
                      ) : (
                        <Badge variant="destructive" className="text-[10px]">Unhealthy</Badge>
                      )}
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive"
                  onClick={() => handleRemove(proxy.url)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
            {proxies.length === 0 && (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No proxies configured
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
