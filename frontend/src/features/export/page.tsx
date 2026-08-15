import { useState } from "react";
import { Download, FileText, Table, Copy, Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export function ExportPage() {
  const [format, setFormat] = useState<"creds" | "csv">("creds");
  const [copied, setCopied] = useState(false);

  const mockPreview = `user1@email.com|Password123|gh_user1
user2@email.com|Password456|gh_user2
user3@email.com|Password789|gh_user3`;

  const handleCopy = () => {
    navigator.clipboard.writeText(mockPreview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Format Selection */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="text-lg">Export Format</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setFormat("creds")}
              className={`flex items-center gap-3 p-4 rounded-lg border transition-all ${
                format === "creds"
                  ? "border-primary bg-primary/5"
                  : "border-border/50 hover:bg-accent/50"
              }`}
            >
              <FileText className="w-5 h-5 text-primary" />
              <div className="text-left">
                <div className="font-medium">Creds</div>
                <div className="text-xs text-muted-foreground">email|password|username</div>
              </div>
            </button>
            <button
              onClick={() => setFormat("csv")}
              className={`flex items-center gap-3 p-4 rounded-lg border transition-all ${
                format === "csv"
                  ? "border-primary bg-primary/5"
                  : "border-border/50 hover:bg-accent/50"
              }`}
            >
              <Table className="w-5 h-5 text-primary" />
              <div className="text-left">
                <div className="font-medium">CSV</div>
                <div className="text-xs text-muted-foreground">email,password,username</div>
              </div>
            </button>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Output Path</label>
            <Input defaultValue={`data/results/creds.${format === "csv" ? "csv" : "txt"}`} />
          </div>
        </CardContent>
      </Card>

      {/* Preview */}
      <Card className="glass-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Preview</CardTitle>
          <div className="flex gap-2">
            <Badge variant="secondary">3 accounts</Badge>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleCopy}>
              {copied ? (
                <Check className="w-4 h-4 text-emerald-500" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <pre className="p-4 rounded-lg bg-muted/50 font-mono text-xs overflow-x-auto">
            {mockPreview}
          </pre>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-3">
        <Button className="gap-2">
          <Download className="w-4 h-4" />
          Export Now
        </Button>
        <Button variant="outline">Copy to Clipboard</Button>
      </div>
    </div>
  );
}
