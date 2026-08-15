"""REST API server for external integration."""

from __future__ import annotations

import logging
import os
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

# API Key authentication
API_KEY = os.getenv("API_KEY", "")


def verify_api_key(key: str = Query(None, alias="api_key")):
    """Verify API key."""
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class RegisterRequest(BaseModel):
    count: int = 1
    proxy: Optional[str] = None
    driver: str = "camoufox"
    headless: bool = False


class AccountResponse(BaseModel):
    username: str
    email: str
    status: str
    created_at: str


@app.get("/api/v1/status")
async def get_status(api_key: str = Query(None)):
    """Get system status."""
    verify_api_key(api_key)
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
    api_key: str = Query(None),
):
    """List accounts."""
    verify_api_key(api_key)
    account_status = AccountStatus(status) if status else None
    accounts = store.list_all(account_status)
    return {
        "accounts": [a.model_dump() for a in accounts[offset:offset + limit]],
        "total": len(accounts),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/v1/accounts/{username}")
async def get_account(username: str, api_key: str = Query(None)):
    """Get single account."""
    verify_api_key(api_key)
    account = store.get(username)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account.model_dump()


@app.post("/api/v1/register")
async def register_accounts(request: RegisterRequest, api_key: str = Query(None)):
    """Start batch registration."""
    verify_api_key(api_key)
    # Would trigger pipeline in background
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
    format: str = Query("creds", regex="^(creds|csv)$"),
    status: str = Query("created"),
    api_key: str = Query(None),
):
    """Export accounts."""
    verify_api_key(api_key)
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
async def delete_account(username: str, api_key: str = Query(None)):
    """Delete account."""
    verify_api_key(api_key)
    # Would need implementation in store
    return {"message": f"Account {username} deleted"}


def run_api_server(host: str = "0.0.0.0", port: int = 8001):
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api_server()
