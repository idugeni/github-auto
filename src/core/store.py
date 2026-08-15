"""Account persistence — JSON + SQLite."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from src.core.account import Account, AccountStatus

log = logging.getLogger(__name__)


class AccountStore:
    """Dual JSON + SQLite account storage."""

    def __init__(self, json_path: str, sqlite_path: Optional[str] = None):
        self._json_path = Path(json_path)
        self._json_path.parent.mkdir(parents=True, exist_ok=True)
        self._sqlite_path = Path(
            sqlite_path or str(self._json_path.with_suffix(".db"))
        )
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        conn = sqlite3.connect(str(self._sqlite_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                email TEXT,
                password TEXT,
                email_password TEXT,
                status TEXT,
                recovery_codes TEXT,
                session_cookies TEXT,
                provider TEXT,
                proxy TEXT,
                error TEXT,
                created_at TEXT,
                verified_at TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _load_json(self) -> list[dict]:
        if not self._json_path.exists():
            return []
        try:
            return json.loads(self._json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Failed to load %s: %s", self._json_path, exc)
            return []

    def _save_json(self, accounts: list[dict]) -> None:
        tmp = self._json_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(accounts, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(self._json_path)

    def save(self, account: Account) -> None:
        """Save account to both stores."""
        data = account.model_dump()

        # SQLite
        conn = sqlite3.connect(str(self._sqlite_path))
        conn.execute(
            """INSERT OR REPLACE INTO accounts
            (username, email, password, email_password, status,
             recovery_codes, session_cookies, provider, proxy,
             error, created_at, verified_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["username"],
                data["email"],
                data["password"],
                data["email_password"],
                data["status"].value if isinstance(data["status"], AccountStatus) else data["status"],
                json.dumps(data["recovery_codes"]),
                json.dumps(data["session_cookies"]),
                data["provider"],
                data["proxy"],
                data["error"],
                data["created_at"],
                data.get("verified_at"),
                json.dumps(data.get("metadata", {})),
            ),
        )
        conn.commit()
        conn.close()

        # JSON
        accounts = self._load_json()
        existing = next(
            (i for i, a in enumerate(accounts) if a.get("username") == account.username),
            None,
        )
        if existing is not None:
            accounts[existing] = data
        else:
            accounts.append(data)
        self._save_json(accounts)

    def get(self, username: str) -> Optional[Account]:
        """Get account by username."""
        conn = sqlite3.connect(str(self._sqlite_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM accounts WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return Account(
            username=row["username"],
            email=row["email"],
            password=row["password"],
            email_password=row["email_password"] or "",
            status=AccountStatus(row["status"]),
            recovery_codes=json.loads(row["recovery_codes"] or "[]"),
            session_cookies=json.loads(row["session_cookies"] or "{}"),
            provider=row["provider"] or "",
            proxy=row["proxy"] or "",
            error=row["error"] or "",
            created_at=row["created_at"] or "",
            verified_at=row["verified_at"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def list_all(self, status: Optional[AccountStatus] = None) -> list[Account]:
        """List all accounts, optionally filtered by status."""
        conn = sqlite3.connect(str(self._sqlite_path))
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute(
                "SELECT * FROM accounts WHERE status = ? ORDER BY created_at",
                (status.value,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM accounts ORDER BY created_at"
            ).fetchall()
        conn.close()
        return [
            Account(
                username=r["username"],
                email=r["email"],
                password=r["password"],
                email_password=r["email_password"] or "",
                status=AccountStatus(r["status"]),
                recovery_codes=json.loads(r["recovery_codes"] or "[]"),
                session_cookies=json.loads(r["session_cookies"] or "{}"),
                provider=r["provider"] or "",
                proxy=r["proxy"] or "",
                error=r["error"] or "",
                created_at=r["created_at"] or "",
                verified_at=r["verified_at"],
                metadata=json.loads(r["metadata"] or "{}"),
            )
            for r in rows
        ]

    def count(self, status: Optional[AccountStatus] = None) -> int:
        conn = sqlite3.connect(str(self._sqlite_path))
        if status:
            row = conn.execute(
                "SELECT COUNT(*) FROM accounts WHERE status = ?",
                (status.value,),
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
        conn.close()
        return row[0]

    def export_creds(self, path: str, status: AccountStatus = AccountStatus.VERIFIED) -> int:
        """Export verified accounts as pipe-delimited file. Returns count."""
        accounts = self.list_all(status)
        lines = [a.to_creds_line() for a in accounts]
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return len(lines)
