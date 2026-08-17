import { useEffect, useState } from "react";
import { Search, Filter, Eye, Trash2, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStore } from "@/lib/store";

const statusColors: Record<string, "success" | "warning" | "destructive" | "secondary"> = {
  created: "success",
  verified: "success",
  failed: "destructive",
  pending: "warning",
};

export function AccountsPage() {
  const { accounts, loading, refreshAccounts } = useStore();
  const [search, setSearch] = useState("");

  useEffect(() => {
    refreshAccounts();
    const interval = setInterval(refreshAccounts, 15000);
    return () => clearInterval(interval);
  }, []);

  const filtered = accounts.filter(
    (a) =>
      a.username.toLowerCase().includes(search.toLowerCase()) ||
      a.email.toLowerCase().includes(search.toLowerCase())
  );

  const created = accounts.filter((a) => a.status === "created").length;
  const failed = accounts.filter((a) => a.status === "failed").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Accounts</h2>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search accounts..."
              className="pl-9 w-64"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-1" />
            Filter
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-sm">
        <span className="text-muted-foreground">
          Total: <span className="font-medium text-foreground">{accounts.length}</span>
        </span>
        <span className="text-muted-foreground">
          Created: <span className="font-medium text-emerald-500">{created}</span>
        </span>
        <span className="text-muted-foreground">
          Failed: <span className="font-medium text-red-500">{failed}</span>
        </span>
      </div>

      {/* Table */}
      <Card className="glass-card">
        <ScrollArea className="h-[calc(100vh-280px)]">
          <div className="p-4">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border/50">
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Username</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Email</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Status</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Created</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((account) => (
                  <tr
                    key={account.username}
                    className="border-b border-border/30 hover:bg-accent/50 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <span className="font-mono text-sm">{account.username}</span>
                    </td>
                    <td className="py-3 px-4 text-sm text-muted-foreground">
                      {account.email}
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={statusColors[account.status]}>
                        {account.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-sm text-muted-foreground">
                      {account.created_at.split("T")[0]}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}
