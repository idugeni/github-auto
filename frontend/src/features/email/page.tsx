import { Mail, CheckCircle2, XCircle, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export function EmailPage() {
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
            <select className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm">
              <option value="lewattok">LewatTok</option>
              <option value="supabase">Supabase</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">LewatTok API Key</label>
            <div className="flex gap-2">
              <Input type="password" placeholder="Enter API key" className="flex-1" />
              <Button variant="outline" size="sm">
                <ExternalLink className="w-4 h-4 mr-1" />
                Get Key
              </Button>
            </div>
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
            <Badge variant="success">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              Configured
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
            <Badge variant="destructive">
              <XCircle className="w-3 h-3 mr-1" />
              Not Configured
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Button>Save Configuration</Button>
    </div>
  );
}
