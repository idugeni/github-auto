import { useState } from "react";
import { Play, Square, Settings2, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { registerAccounts, getStatus } from "@/lib/tauri-ipc";

export function RegisterPage() {
  const [count, setCount] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<{ success: number; failed: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    setIsRunning(true);
    setResult(null);
    setError(null);

    try {
      await registerAccounts(count);
      const status = await getStatus();
      setResult({ success: status.created, failed: status.failed });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Registration failed");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Config */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Settings2 className="w-5 h-5" />
            Registration Config
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Number of Accounts</label>
              <Input
                type="number"
                min={1}
                max={100}
                value={count}
                onChange={(e) => setCount(parseInt(e.target.value) || 1)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Email Provider</label>
              <Input defaultValue="lewattok" disabled />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {isRunning ? "Registering..." : result ? "Complete" : "Ready"}
            </span>
            {isRunning && <Loader2 className="w-4 h-4 animate-spin" />}
          </div>

          {result && (
            <div className="flex gap-4 text-xs">
              <span>Success: <Badge variant="success">{result.success}</Badge></span>
              <span>Failed: <Badge variant="destructive">{result.failed}</Badge></span>
            </div>
          )}

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-lg">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        {!isRunning ? (
          <Button onClick={handleStart} className="gap-2">
            <Play className="w-4 h-4" />
            Start Registration
          </Button>
        ) : (
          <Button variant="destructive" disabled className="gap-2">
            <Square className="w-4 h-4" />
            Running...
          </Button>
        )}
      </div>
    </div>
  );
}
