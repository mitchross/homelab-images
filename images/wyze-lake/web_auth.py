"""Refresh Wyze Web View authentication and retain the rotated session cookie."""

import base64
import hashlib
import json
import os
import re
import ssl
import tempfile
import time
import urllib.error
import urllib.request
from http.cookies import SimpleCookie
from pathlib import Path

from protocol import USER_AGENT

REFRESH_URL = "https://services.wyze.com/api/v2/santa/refresh?tag=webview"


class WebLoginRequired(RuntimeError):
    """A new official Web View login is required."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_cookie(value):
    if not value or not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
        raise ValueError("Invalid Web View session cookie")
    return value


def token_auth(token, now):
    if not isinstance(token, str) or len(token.split(".")) != 3:
        raise ValueError("Invalid Web View access token")
    # Claims come from Wyze over verified TLS; use them only for expiry and camera controls.
    claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "==="))
    if (
        not isinstance(claims, dict)
        or claims.get("iss") != "https://auth.wyze.com"
        or "native" not in claims.get("scope", [])
        or not claims.get("user_id")
        or not isinstance(claims.get("exp"), int)
        or claims["exp"] <= now + 60
    ):
        raise ValueError("Invalid Web View access token")
    return {
        "access_token": token,
        "user_id": claims["user_id"],
        "expires_at": claims["exp"],
    }


class WebSessionAuth:
    def __init__(self, seed_path, state_path):
        self.seed_path = Path(seed_path)
        self.state_path = Path(state_path)
        self.state = None

    def load(self):
        seed = validate_cookie(self.seed_path.read_text().strip())
        fingerprint = hashlib.sha256(seed.encode()).hexdigest()
        if self.state is None:
            try:
                self.state = json.loads(self.state_path.read_text())
            except (FileNotFoundError, json.JSONDecodeError):
                self.state = {}
            if not isinstance(self.state, dict):
                self.state = {}
        # A new projected Secret replaces a revoked login without replacing the pod.
        if self.state.get("seed_sha256") != fingerprint:
            self.state = {"seed_sha256": fingerprint, "cookie": seed}
        return self.state

    def save(self):
        parent = self.state_path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(parent, 0o700)
        fd, temporary = tempfile.mkstemp(dir=parent, prefix=".web-session-")
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(self.state, stream, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_path)
            directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def refresh(self, now):
        cookie = validate_cookie(self.state["cookie"])
        request = urllib.request.Request(
            REFRESH_URL,
            headers={
                "Cookie": "session=" + cookie,
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
                "Origin": "https://my.wyze.com",
                "Referer": "https://my.wyze.com/",
            },
        )
        opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context())
        )
        with opener.open(request, timeout=15) as response:
            data = json.load(response)
            auth = token_auth(data["access_token"], now)
            cookies = SimpleCookie()
            for header in response.headers.get_all("Set-Cookie", []):
                cookies.load(header)
            renewed = cookies.get("session")
            if renewed is None or renewed["domain"] not in ("", "services.wyze.com"):
                raise ValueError("Missing renewed Web View session")
            value = validate_cookie(renewed.value)
        self.state.update(cookie=value, auth=auth, refreshed_at=now)
        self.state.pop("retry_at", None)
        self.state.pop("login_required", None)
        self.save()
        print(json.dumps({"event": "web_auth_refreshed"}), flush=True)

    def auth(self):
        state = self.load()
        now = time.time()
        auth = state.get("auth", {})
        usable = auth.get("expires_at", 0) > now + 60
        if now < state.get("retry_at", 0):
            if usable and not state.get("login_required"):
                return auth
            if state.get("login_required"):
                raise WebLoginRequired("Refresh the saved Web View session")
            raise RuntimeError("Web View refresh retry is delayed")
        if usable and now - state.get("refreshed_at", 0) < 3600 and auth["expires_at"] > now + 300:
            return auth
        try:
            self.refresh(now)
        except (urllib.error.URLError, TimeoutError) as error:
            login_required = isinstance(error, urllib.error.HTTPError) and error.code in (400, 401, 403)
            state.update(retry_at=now + (300 if login_required else 60), login_required=login_required)
            self.save()
            if login_required:
                raise WebLoginRequired("Refresh the saved Web View session") from None
            if usable:
                return auth
            raise RuntimeError("Web View refresh is unavailable") from None
        except (ValueError, KeyError, IndexError, TypeError):
            state.update(retry_at=now + 300, login_required=True)
            self.save()
            raise WebLoginRequired("Unexpected Web View refresh response") from None
        return self.state["auth"]

    def invalidate(self):
        self.load()
        self.state.get("auth", {})["expires_at"] = 0
        self.save()
