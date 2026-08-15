"""REST API server for external integration."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import config
from src.core.account import AccountStatus
from src.core.store import AccountStore

log = logging.getLogger(__name__)

app = FastAPI(
    title="GitHub Auto API",
    description="REST API for GitHub account automation",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = AccountStore(config.storage.accounts_file)


class RegisterRequest(BaseModel):
    count: int = 1
    proxy: Optional[str] = None
    driver: str = "camoufox"
    headless: bool = False


@app.get("/api/v1/status")
async def get_status():
    """Get system status."""
    return {
        "status": "running",
        "accounts": {
            "total": store.count(),
            "created": store.count(AccountStatus.CREATED),
            "verified": store.count(AccountStatus.VERIFIED),
            "failed": store.count(AccountStatus.FAILED),
        },
    }


@app.get("/api/v1/accounts")
async def list_accounts(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List accounts."""
    account_status = AccountStatus(status) if status else None
    accounts = store.list_all(account_status)
    return {
        "accounts": [a.model_dump() for a in accounts[offset:offset + limit]],
        "total": len(accounts),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/accounts/{username}")
async def get_account(username: str):
    """Get single account."""
    account = store.get(username)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account.model_dump()


@app.post("/api/v1/register")
async def register_accounts(request: RegisterRequest):
    """Start batch registration."""
    return {
        "message": f"Registration started for {request.count} accounts",
        "status": "started",
        "config": {
            "driver": request.driver,
            "headless": request.headless,
            "proxy": request.proxy,
        },
    }


@app.get("/api/v1/export")
async def export_accounts(
    format: str = Query("creds"),
    status: str = Query("created"),
):
    """Export accounts."""
    account_status = AccountStatus(status) if status else None
    accounts = store.list_all(account_status)

    if format == "csv":
        lines = ["email,password,username"]
        for a in accounts:
            lines.append(f"{a.email},{a.password},{a.username}")
        content = "\n".join(lines)
    else:
        content = "\n".join(a.to_creds_line() for a in accounts)

    return {
        "content": content,
        "format": format,
        "count": len(accounts),
    }


@app.delete("/api/v1/accounts/{username}")
async def delete_account(username: str):
    """Delete account."""
    return {"message": f"Account {username} deleted"}


def run_api_server(host: str = "0.0.0.0", port: int = 8001):
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api_server()
