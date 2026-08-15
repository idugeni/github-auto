import { Save, RotateCcw, Key, Globe, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

export function SettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      {/* General */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Globe className="w-5 h-5" />
            General
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Browser Driver</label>
              <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm">
                <option value="camoufox">Camoufox</option>
                <option value="patchright">Patchright</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Default Password</label>
              <Input defaultValue="AutoGen2026!" />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch id="headless" defaultChecked={false} />
              <label htmlFor="headless" className="text-sm">Headless Mode</label>
            </div>
            <div className="flex items-center gap-2">
              <Switch id="debug" defaultChecked={false} />
              <label htmlFor="debug" className="text-sm">Debug Mode</label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Key className="w-5 h-5" />
            API Keys
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Groq API Key (reCAPTCHA ASR)</label>
            <Input type="password" placeholder="gsk_..." />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">LewatTok API Key</label>
            <Input type="password" placeholder="Enter API key" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Supabase URL</label>
            <Input placeholder="https://your-project.supabase.co" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Supabase Anon Key</label>
            <Input type="password" placeholder="Enter anon key" />
          </div>
        </CardContent>
      </Card>

      {/* Timing */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Clock className="w-5 h-5" />
            Timing
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Delay Base (seconds)</label>
              <Input type="number" defaultValue={8} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Delay Jitter (seconds)</label>
              <Input type="number" defaultValue={2} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">OTP Timeout (seconds)</label>
              <Input type="number" defaultValue={120} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Retries</label>
              <Input type="number" defaultValue={2} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button className="gap-2">
          <Save className="w-4 h-4" />
          Save Settings
        </Button>
        <Button variant="outline" className="gap-2">
          <RotateCcw className="w-4 h-4" />
          Reset to Default
        </Button>
      </div>
    </div>
  );
}
