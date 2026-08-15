import { useState } from "react";
import { Play, Square, Settings2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";

export function RegisterPage() {
  const [count, setCount] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleStart = () => {
    setIsRunning(true);
    setProgress(0);
    // Mock progress
    const interval = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return p + 10;
      });
    }, 500);
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
              <label className="text-sm font-medium">Browser Driver</label>
              <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm">
                <option value="camoufox">Camoufox</option>
                <option value="patchright">Patchright</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Email Provider</label>
              <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm">
                <option value="lewattok">LewatTok</option>
                <option value="supabase">Supabase</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Proxy</label>
              <Input placeholder="socks5://user:pass@host:1080" />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch id="headless" />
              <label htmlFor="headless" className="text-sm">Headless Mode</label>
            </div>
            <div className="flex items-center gap-2">
              <Switch id="debug" />
              <label htmlFor="debug" className="text-sm">Debug Screenshots</label>
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
              {isRunning ? "Registering..." : progress === 100 ? "Complete" : "Ready"}
            </span>
            <span className="font-mono">
              {progress}%
            </span>
          </div>

          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>Success: <Badge variant="success">0</Badge></span>
            <span>Failed: <Badge variant="destructive">0</Badge></span>
            <span>Pending: <Badge variant="secondary">{count}</Badge></span>
          </div>
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
          <Button variant="destructive" onClick={() => setIsRunning(false)} className="gap-2">
            <Square className="w-4 h-4" />
            Stop
          </Button>
        )}
        <Button variant="outline">Save Config</Button>
      </div>
    </div>
  );
}
