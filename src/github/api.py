"""Minimal GitHub REST API client."""

from __future__ import annotations

import logging
from typing import Optional

from src.utils.http import HttpClient

log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GithubApiClient:
    """Minimal GitHub API client for account operations."""

    def __init__(self, token: Optional[str] = None, proxy: Optional[str] = None):
        self._http = HttpClient(proxy=proxy)
        self._token = token

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def get_user(self, username: Optional[str] = None) -> Optional[dict]:
        """Get user info. If no username, get authenticated user."""
        endpoint = "/user" if not username else f"/users/{username}"
        resp = self._http.get(f"{GITHUB_API}{endpoint}", headers=self._headers())
        if resp.status_code == 200:
            return resp.json()
        log.debug("Get user failed: %s", resp.status_code)
        return None

    def get_rate_limit(self) -> Optional[dict]:
        """Check API rate limit."""
        resp = self._http.get(f"{GITHUB_API}/rate_limit", headers=self._headers())
        if resp.status_code == 200:
            return resp.json()
        return None

    def create_repo(self, name: str, private: bool = True) -> Optional[dict]:
        """Create a new repository."""
        resp = self._http.post(
            f"{GITHUB_API}/user/repos",
            json={"name": name, "private": private},
            headers=self._headers(),
        )
        if resp.status_code == 201:
            return resp.json()
        log.debug("Create repo failed: %s %s", resp.status_code, resp.text[:100])
        return None

    def get_repos(self, per_page: int = 30) -> list[dict]:
        """List authenticated user's repos."""
        resp = self._http.get(
            f"{GITHUB_API}/user/repos",
            params={"per_page": per_page, "sort": "updated"},
            headers=self._headers(),
        )
        if resp.status_code == 200:
            return resp.json()
        return []
