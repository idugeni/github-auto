import {
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Globe,
  Play,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface DashboardPageProps {
  onNavigate: (page: string) => void;
}

const stats = [
  { label: "Total Accounts", value: "0", icon: Users, color: "text-blue-500" },
  { label: "Created", value: "0", icon: CheckCircle2, color: "text-emerald-500" },
  { label: "Failed", value: "0", icon: XCircle, color: "text-red-500" },
  { label: "Active Proxies", value: "0", icon: Globe, color: "text-amber-500" },
];

const quickActions = [
  { label: "Register Accounts", page: "register", icon: Play, description: "Start batch registration" },
  { label: "View Accounts", page: "accounts", icon: Users, description: "Browse account list" },
  { label: "Check Logs", page: "logs", icon: Clock, description: "View real-time logs" },
  { label: "Export Data", page: "export", icon: ArrowRight, description: "Export to file" },
];

export function DashboardPage({ onNavigate }: DashboardPageProps) {
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
