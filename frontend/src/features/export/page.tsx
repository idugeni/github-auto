import { useState } from "react";
import { Download, FileText, Table, Copy, Check, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { exportAccounts, getAccounts } from "@/lib/tauri-ipc";

export function ExportPage() {
  const [format, setFormat] = useState<"creds" | "csv">("creds");
  const [outputPath, setOutputPath] = useState("data/results/creds.txt");
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setResult(null);
    try {
      await exportAccounts(format, outputPath);
      setResult(`Exported to ${outputPath}`);
    } catch (e: unknown) {
      setResult(`Error: ${e instanceof Error ? e.message : "Export failed"}`);
    } finally {
      setExporting(false);
    }
  };

  const handleCopy = async () => {
    try {
      const accounts = await getAccounts();
      const lines = accounts.map((a) =>
        format === "csv"
          ? `${a.email},${a.password},${a.username}`
          : `${a.email}|${a.password}|${a.username}`
      );
      navigator.clipboard.writeText(lines.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error("Copy failed:", e);
    }
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
              onClick={() => { setFormat("creds"); setOutputPath("data/results/creds.txt"); }}
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
              onClick={() => { setFormat("csv"); setOutputPath("data/results/creds.csv"); }}
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
            <Input
              value={outputPath}
              onChange={(e) => setOutputPath(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Result */}
      {result && (
        <Card className="glass-card">
          <CardContent className="pt-6">
            <div className={`text-sm ${result.startsWith("Error") ? "text-destructive" : "text-emerald-500"}`}>
              {result}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={handleExport} disabled={exporting} className="gap-2">
          {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          Export Now
        </Button>
        <Button variant="outline" onClick={handleCopy} className="gap-2">
          {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
          {copied ? "Copied!" : "Copy to Clipboard"}
        </Button>
      </div>
    </div>
  );
}
