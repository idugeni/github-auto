import { Plus, Trash2, RefreshCw, Globe, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const mockProxies = [
  { url: "socks5://user:pass@us1.proxy.com:1080", country: "US", healthy: true },
  { url: "socks5://user:pass@de1.proxy.com:1080", country: "DE", healthy: true },
  { url: "http://user:pass@jp1.proxy.com:8080", country: "JP", healthy: false },
];

export function ProxiesPage() {
  return (
    <div className="space-y-4 max-w-3xl">
      {/* Add Proxy */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Add Proxy</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input placeholder="protocol://user:pass@host:port|Country" className="flex-1" />
            <Button>
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
              2 Healthy
            </Badge>
            <Badge variant="destructive">
              <XCircle className="w-3 h-3 mr-1" />
              1 Unhealthy
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {mockProxies.map((proxy) => (
              <div
                key={proxy.url}
                className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Globe className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <span className="font-mono text-sm">{proxy.url}</span>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="outline" className="text-[10px]">
                        {proxy.country}
                      </Badge>
                      {proxy.healthy ? (
                        <Badge variant="success" className="text-[10px]">Healthy</Badge>
                      ) : (
                        <Badge variant="destructive" className="text-[10px]">Unhealthy</Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
