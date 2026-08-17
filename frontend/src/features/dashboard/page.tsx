import { useEffect } from "react";
import {
  Users,
  CheckCircle2,
  XCircle,
  Globe,
  Play,
  ArrowRight,
  Loader2,
  Clock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";

interface DashboardPageProps {
  onNavigate: (page: string) => void;
}

const quickActions = [
  { label: "Register Accounts", page: "register", icon: Play, description: "Start batch registration" },
  { label: "View Accounts", page: "accounts", icon: Users, description: "Browse account list" },
  { label: "Check Logs", page: "logs", icon: Clock, description: "View real-time logs" },
  { label: "Export Data", page: "export", icon: ArrowRight, description: "Export to file" },
];

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const { status, proxies, loading, refreshStatus, refreshProxies } = useStore();

  useEffect(() => {
    refreshStatus();
    refreshProxies();
    const interval = setInterval(() => {
      refreshStatus();
      refreshProxies();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { label: "Total Accounts", value: status.total, icon: Users, color: "text-blue-500" },
    { label: "Created", value: status.created, icon: CheckCircle2, color: "text-emerald-500" },
    { label: "Failed", value: status.failed, icon: XCircle, color: "text-red-500" },
    { label: "Active Proxies", value: proxies.filter((p) => p.healthy).length, icon: Globe, color: "text-amber-500" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label} className="glass-card-hover">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <Icon className={`w-4 h-4 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Button
                  key={action.label}
                  variant="outline"
                  className="h-auto flex-col items-start p-4 glass-card-hover border-0"
                  onClick={() => onNavigate(action.page)}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className="w-4 h-4 text-primary" />
                    <span className="font-medium">{action.label}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {action.description}
                  </span>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No recent activity</p>
            <p className="text-xs mt-1">
              Start registration to see activity here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
