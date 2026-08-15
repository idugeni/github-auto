"""curl_cffi HTTP wrapper with TLS fingerprint impersonation."""

from __future__ import annotations

import logging
from typing import Any, Optional

from curl_cffi.requests import Session

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20
MAX_RETRIES = 1


class HttpClient:
    """HTTP client with Chrome TLS impersonation."""

    def __init__(
        self,
        impersonate: str = "chrome131",
        proxy: Optional[str] = None,
    ):
        self._impersonate = impersonate
        self._proxy = proxy

    def _new_session(self) -> Session:
        session = Session(impersonate=self._impersonate)  # type: ignore[arg-type]
        if self._proxy:
            session.proxies = {
                "http": self._proxy,
                "https": self._proxy,
            }
        return session

    def get(
        self,
        url: str,
        session: Optional[Session] = None,
        **kwargs: Any,
    ):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        kwargs.setdefault("allow_redirects", False)
        sess = session or self._new_session()
        try:
            return sess.get(url, **kwargs)
        except Exception as exc:
            if MAX_RETRIES > 0:
                log.warning("GET %s failed, retrying: %s", url, exc)
                return sess.get(url, **kwargs)
            raise

    def post(
        self,
        url: str,
        session: Optional[Session] = None,
        **kwargs: Any,
    ):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        kwargs.setdefault("allow_redirects", False)
        sess = session or self._new_session()
        try:
            return sess.post(url, **kwargs)
        except Exception as exc:
            if MAX_RETRIES > 0:
                log.warning("POST %s failed, retrying: %s", url, exc)
                return sess.post(url, **kwargs)
            raise
