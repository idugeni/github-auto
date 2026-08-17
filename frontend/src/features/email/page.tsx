import { useEffect, useState } from "react";
import { Mail, CheckCircle2, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getConfig, updateConfig } from "@/lib/tauri-ipc";
import type { AppConfig } from "@/lib/tauri-ipc";

export function EmailPage() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const data = await getConfig();
      setConfig(data);
    } catch (e) {
      console.error("Failed to load config:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!config) return;
    setSaving(true);
    try {
      await updateConfig("email_provider", config.email_provider);
    } catch (e) {
      console.error("Failed to save:", e);
    } finally {
      setSaving(false);
    }
  }

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Provider Selection */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Email Provider</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Active Provider</label>
            <select
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
              value={config.email_provider}
              onChange={(e) => setConfig({ ...config, email_provider: e.target.value })}
            >
              <option value="lewattok">LewatTok</option>
              <option value="supabase">Supabase</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Status */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Provider Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg border border-border/50">
            <div className="flex items-center gap-3">
              <Mail className="w-4 h-4 text-muted-foreground" />
              <div>
                <span className="text-sm font-medium">LewatTok</span>
                <div className="text-xs text-muted-foreground">api.lewattok.web.id</div>
              </div>
            </div>
            <Badge variant={config.email_provider === "lewattok" ? "success" : "secondary"}>
              {config.email_provider === "lewattok" ? (
                <><CheckCircle2 className="w-3 h-3 mr-1" /> Active</>
              ) : "Standby"}
            </Badge>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg border border-border/50">
            <div className="flex items-center gap-3">
              <Mail className="w-4 h-4 text-muted-foreground" />
              <div>
                <span className="text-sm font-medium">Supabase</span>
                <div className="text-xs text-muted-foreground">Edge Functions</div>
              </div>
            </div>
            <Badge variant={config.email_provider === "supabase" ? "success" : "secondary"}>
              {config.email_provider === "supabase" ? (
                <><CheckCircle2 className="w-3 h-3 mr-1" /> Active</>
              ) : "Standby"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={saving} className="gap-2">
        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
        Save Configuration
      </Button>
    </div>
  );
}
