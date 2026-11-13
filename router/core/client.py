"""Router session: token -> login -> read pages -> logout. Read-only by construction.

The only non-GET requests ever sent are the three auth calls below (token, login,
logout). Commands get a session whose sole data method is get(), which refuses
anything that looks like an action endpoint (.cgi).
"""
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager

from core import creds

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Lock and auth-failed latch. Under systemd (StateDirectory=) the install dir is read-only,
# so use the dir systemd provides; otherwise <project>/.state.
STATE_DIR = (os.environ.get("STATE_DIRECTORY", "").split(":")[0]
             or os.path.join(ROOT, ".state"))
AUTH_FAILED = os.path.join(STATE_DIR, "auth-failed")
LOCK_FILE = os.path.join(STATE_DIR, "lock")
TIMEOUT = 10
LANG_COOKIE = "body:Language:english:id=-1"


class RouterError(Exception):
    """kind/exit_code form the contract with callers (see AGENTS.md)."""

    def __init__(self, kind, exit_code, message):
        super().__init__(message)
        self.kind = kind
        self.exit_code = exit_code


def busy(msg):
    return RouterError("busy", 2, msg)


def rejected(msg):
    return RouterError("rejected", 3, msg)


def blocked(msg):
    return RouterError("blocked", 4, msg)


def failure(msg):
    return RouterError("failure", 5, msg)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _is_login_page(body):
    return "txt_Password" in body


class Session:
    def __init__(self, host):
        self._base = "http://" + host
        self._opener = urllib.request.build_opener(_NoRedirect)
        self._cookies = {}
        self._page_token = None
        self._pages = {}

    # -- public: the only thing commands may call ---------------------------
    def get(self, path):
        """GET a page (cached per run). Refuses action endpoints; raises if the session died."""
        if ".cgi" in path.lower():
            raise failure("refusing to GET action endpoint: " + path)
        if path not in self._pages:
            status, body = self._send("GET", path)
            if status != 200 or _is_login_page(body):
                raise failure("GET %s failed (HTTP %s or session lost)" % (path, status))
            self._pages[path] = body
        return self._pages[path]

    # -- auth ---------------------------------------------------------------
    def _send(self, method, path, form=None):
        headers = {"User-Agent": "Mozilla/5.0", "Referer": self._base + "/"}
        if self._cookies:
            headers["Cookie"] = "; ".join("%s=%s" % kv for kv in self._cookies.items())
        data = None
        if method == "POST":
            data = urllib.parse.urlencode(form or {}).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(self._base + path, data=data, headers=headers, method=method)
        try:
            resp = self._opener.open(req, timeout=TIMEOUT)
        except urllib.error.HTTPError as e:
            resp = e
        except (urllib.error.URLError, OSError) as e:
            raise failure("router unreachable: %s" % e)
        for cookie in resp.headers.get_all("Set-Cookie") or []:
            name, _, rest = cookie.partition("=")
            self._cookies[name.strip()] = rest.split(";", 1)[0]
        return resp.status, resp.read().decode("utf-8", "replace")

    def _login(self, user, password):
        status, token = self._send("POST", "/asp/GetRandCount.asp")
        token = token.lstrip("﻿").strip()
        if status != 200 or not re.fullmatch(r"[0-9a-fA-F]{16,128}", token):
            raise failure("unexpected login token response (HTTP %s)" % status)

        self._cookies = {"Cookie": LANG_COOKIE}
        self._send("POST", "/login.cgi", {
            "UserName": user,
            "PassWord": base64.b64encode(password.encode()).decode(),
            "Language": "english",
            "x.X_HW_Token": token,
        })

        status, index = self._send("GET", "/index.asp")
        if status == 200 and not _is_login_page(index) and "CookieHttp" in self._cookies:
            m = re.search(r'id="(?:hwonttoken|onttoken)"[^>]*value="([0-9a-fA-F]+)"', index)
            self._page_token = m.group(1) if m else None
            return
        self._classify_login_failure()

    def _classify_login_failure(self):
        """Wrong password bumps the router's LoginTimes counter; a busy slot does not."""
        self._cookies = {}
        _, page = self._send("GET", "/")
        times = re.search(r"var LoginTimes = '(\d*)'", page)
        lock_left = re.search(r"var LockLeftTime = '(\d*)'", page)
        times = int(times.group(1) or 0) if times else 0
        lock_left = int(lock_left.group(1) or 0) if lock_left else 0
        if lock_left > 0:
            raise blocked("router is locking logins for %ss" % lock_left)
        if times > 0:
            raise rejected("login rejected (router failed-login counter = %s)" % times)
        raise busy("login not accepted and no failure counted; admin slot likely in use")

    def _logout(self):
        if not self._page_token:
            return False
        try:
            self._send("POST", "/logout.cgi?RequestFile=html/logout.html",
                       {"x.X_HW_Token": self._page_token})
            status, _ = self._send("GET", "/index.asp")
            return status != 200
        except RouterError:
            return False


@contextmanager
def _exclusive():
    """Serialise runs so concurrent watchers never log in at the same time."""
    with open(LOCK_FILE, "a+") as f:
        try:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)
        except ImportError:  # Windows dev box only: no cross-process lock
            pass
        yield


@contextmanager
def session():
    """Logged-in Session for the duration of the block; always logs out."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with _exclusive():
        # Checked under the lock: a run that waited on another run's rejected login
        # must see the latch it wrote, not log in again and burn a second strike.
        if os.path.exists(AUTH_FAILED):
            raise blocked("previous login was rejected; fix credentials, then delete .state/auth-failed")
        host, user, password = creds.load(ROOT)
        s = Session(host)
        try:
            s._login(user, password)
        except RouterError as e:
            if e.kind in ("rejected", "blocked"):
                with open(AUTH_FAILED, "w") as f:
                    json.dump({"kind": e.kind, "message": str(e)}, f)
            raise
        try:
            yield s
        finally:
            if not s._logout():
                import sys
                sys.stderr.write("warning: logout not confirmed; router session may linger until idle timeout\n")
