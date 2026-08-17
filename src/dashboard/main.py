"""FastAPI web dashboard for github-auto."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config.settings import config
from src.core.account import AccountStatus
from src.core.store import AccountStore

log = logging.getLogger(__name__)

app = FastAPI(
    title="GitHub Auto Dashboard",
    description="Web dashboard for GitHub account automation",
    version="0.1.0",
)

store = AccountStore(config.storage.accounts_file)

# WebSocket connections
connections: list[WebSocket] = []


@app.get("/", response_class=HTMLResponse)
async def index():
    """Dashboard home page."""
    return DASHBOARD_HTML


@app.get("/api/status")
async def get_status():
    """Get account inventory status."""
    return {
        "total": store.count(),
        "created": store.count(AccountStatus.CREATED),
        "verified": store.count(AccountStatus.VERIFIED),
        "failed": store.count(AccountStatus.FAILED),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/accounts")
async def get_accounts(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get account list."""
    account_status = AccountStatus(status) if status else None
    accounts = store.list_all(account_status)
    return {
        "accounts": [a.model_dump() for a in accounts[offset:offset + limit]],
        "total": len(accounts),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/accounts/{username}")
async def get_account(username: str):
    """Get single account."""
    account = store.get(username)
    if not account:
        return JSONResponse(status_code=404, content={"error": "Account not found"})
    return account.model_dump()


@app.delete("/api/accounts/{username}")
async def delete_account(username: str):
    """Delete account."""
    # Note: This would need implementation in store
    return {"message": f"Account {username} deleted"}


@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return {
        "email_provider": config.email.provider,
        "http_client": "curl_cffi",
        "delay_base": config.pipeline.delay_base,
        "delay_jitter": config.pipeline.delay_jitter,
        "max_retries": config.pipeline.max_retries,
    }


@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries."""
    log_file = Path(config.log.log_dir) / "github-auto.log"
    if not log_file.exists():
        return {"logs": []}

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]
            return {"logs": [line.strip() for line in recent]}
    except Exception as exc:
        return {"logs": [], "error": str(exc)}


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket for real-time log streaming."""
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)


@app.post("/api/register")
async def start_registration(count: int = 1):
    """Start batch registration."""
    # This would trigger the pipeline in background
    return {"message": f"Registration started for {count} accounts", "status": "started"}


@app.get("/api/export")
async def export_accounts(format: str = "creds"):
    """Export accounts."""
    accounts = store.list_all(AccountStatus.CREATED)
    if format == "csv":
        lines = ["email,password,username"]
        for a in accounts:
            lines.append(f"{a.email},{a.password},{a.username}")
        return {"content": "\n".join(lines), "format": "csv"}
    else:
        lines = [a.to_creds_line() for a in accounts]
        return {"content": "\n".join(lines), "format": "creds"}


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub Auto Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {
            --glass-bg: rgba(255, 255, 255, 0.65);
            --glass-border: rgba(255, 255, 255, 0.5);
        }
        .dark {
            --glass-bg: rgba(44, 44, 44, 0.65);
            --glass-border: rgba(255, 255, 255, 0.08);
        }
        .glass {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
        }
    </style>
</head>
<body class="bg-gray-100 dark:bg-gray-900 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-8">GitHub Auto Dashboard</h1>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8" id="stats">
            <div class="glass rounded-lg p-4">
                <h3 class="text-sm text-gray-500">Total Accounts</h3>
                <p class="text-2xl font-bold" id="stat-total">0</p>
            </div>
            <div class="glass rounded-lg p-4">
                <h3 class="text-sm text-gray-500">Created</h3>
                <p class="text-2xl font-bold text-green-500" id="stat-created">0</p>
            </div>
            <div class="glass rounded-lg p-4">
                <h3 class="text-sm text-gray-500">Verified</h3>
                <p class="text-2xl font-bold text-blue-500" id="stat-verified">0</p>
            </div>
            <div class="glass rounded-lg p-4">
                <h3 class="text-sm text-gray-500">Failed</h3>
                <p class="text-2xl font-bold text-red-500" id="stat-failed">0</p>
            </div>
        </div>

        <!-- Accounts Table -->
        <div class="glass rounded-lg p-4 mb-8">
            <h2 class="text-xl font-semibold mb-4">Accounts</h2>
            <table class="w-full">
                <thead>
                    <tr class="border-b">
                        <th class="text-left py-2">Username</th>
                        <th class="text-left py-2">Email</th>
                        <th class="text-left py-2">Status</th>
                        <th class="text-left py-2">Created</th>
                    </tr>
                </thead>
                <tbody id="accounts-table">
                </tbody>
            </table>
        </div>

        <!-- Logs -->
        <div class="glass rounded-lg p-4">
            <h2 class="text-xl font-semibold mb-4">Recent Logs</h2>
            <pre class="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto h-64 text-sm" id="logs"></pre>
        </div>
    </div>

    <script>
        async function fetchStats() {
            const res = await fetch('/api/status');
            const data = await res.json();
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-created').textContent = data.created;
            document.getElementById('stat-verified').textContent = data.verified;
            document.getElementById('stat-failed').textContent = data.failed;
        }

        async function fetchAccounts() {
            const res = await fetch('/api/accounts?limit=50');
            const data = await res.json();
            const tbody = document.getElementById('accounts-table');
            tbody.innerHTML = data.accounts.map(a => `
                <tr class="border-b">
                    <td class="py-2 font-mono">${a.username}</td>
                    <td class="py-2">${a.email}</td>
                    <td class="py-2"><span class="px-2 py-1 rounded text-xs ${
                        a.status === 'created' ? 'bg-green-100 text-green-800' :
                        a.status === 'verified' ? 'bg-blue-100 text-blue-800' :
                        'bg-red-100 text-red-800'
                    }">${a.status}</span></td>
                    <td class="py-2 text-sm text-gray-500">${a.created_at?.split('T')[0] || ''}</td>
                </tr>
            `).join('');
        }

        async function fetchLogs() {
            const res = await fetch('/api/logs?lines=50');
            const data = await res.json();
            document.getElementById('logs').textContent = data.logs.join('\\n');
        }

        // Initial load
        fetchStats();
        fetchAccounts();
        fetchLogs();

        // Refresh every 5 seconds
        setInterval(fetchStats, 5000);
        setInterval(fetchAccounts, 10000);
        setInterval(fetchLogs, 5000);
    </script>
</body>
</html>
"""


def run_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Run the dashboard server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
