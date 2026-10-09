"""Exercise credential rotation, restart recovery, and failed refresh behavior."""

import base64
import io
import json
import stat
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import Mock, patch

from protocol import WyzeAPI
from web_auth import WebLoginRequired, WebSessionAuth

NOW = 1800000000


def token(exp=NOW + 7200, scope=None):
    claims = {
        "iss": "https://auth.wyze.com",
        "scope": ["native"] if scope is None else scope,
        "user_id": "test-user",
        "exp": exp,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return "header." + encoded + ".signature"


def response(cookie="rotated-cookie", access_token=None):
    headers = Message()
    headers.add_header("Set-Cookie", "session=" + cookie + "; Secure; HttpOnly; Path=/")
    body = io.BytesIO(json.dumps({"access_token": access_token or token()}).encode())
    body.headers = headers
    return body


class WebAuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.seed = self.root / "seed"
        self.seed.write_text("seed-cookie")
        self.state = self.root / "private" / "state.json"
        self.auth = WebSessionAuth(self.seed, self.state)
        self.opener = Mock()
        self.network = patch("web_auth.urllib.request.build_opener", return_value=self.opener)
        self.network.start()
        self.addCleanup(self.network.stop)
        self.clock = patch("web_auth.time.time", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def refresh(self, cookie="rotated-cookie", access_token=None):
        self.opener.open.return_value = response(cookie, access_token)
        return self.auth.auth()

    def test_rotation_survives_restart_and_uses_private_files(self):
        self.refresh()
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.state.parent.stat().st_mode), 0o700)
        self.assertEqual(list(self.state.parent.iterdir()), [self.state])
        self.auth = WebSessionAuth(self.seed, self.state)
        self.assertEqual(self.auth.auth()["user_id"], "test-user")
        self.assertEqual(self.opener.open.call_count, 1)
        with patch("web_auth.time.time", return_value=NOW + 3601):
            self.refresh("second-cookie", token(NOW + 10000))
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.get_header("Cookie"), "session=rotated-cookie")
        self.assertEqual(json.loads(self.state.read_text())["cookie"], "second-cookie")

    def test_projected_secret_reenrolls_without_restart(self):
        self.refresh()
        self.seed.write_text("new-login-cookie")
        self.refresh("new-rotated-cookie")
        self.assertEqual(self.opener.open.call_args.args[0].get_header("Cookie"), "session=new-login-cookie")

    def test_revoked_session_backoff_survives_restart(self):
        self.opener.open.side_effect = urllib.error.HTTPError("test", 401, "denied", {}, None)
        with self.assertRaises(WebLoginRequired):
            self.auth.auth()
        self.auth = WebSessionAuth(self.seed, self.state)
        with self.assertRaises(WebLoginRequired):
            self.auth.auth()
        self.assertEqual(self.opener.open.call_count, 1)

    def test_network_failure_keeps_usable_token_and_delays_retry(self):
        old = self.refresh()
        self.opener.open.side_effect = urllib.error.URLError("offline")
        with patch("web_auth.time.time", return_value=NOW + 3601):
            self.assertEqual(self.auth.auth(), old)
            self.assertEqual(self.auth.auth(), old)
        self.assertEqual(self.opener.open.call_count, 2)

    def test_network_failure_does_not_return_expired_auth(self):
        self.refresh()
        self.opener.open.side_effect = urllib.error.URLError("offline")
        with patch("web_auth.time.time", return_value=NOW + 7300):
            with self.assertRaises(RuntimeError):
                self.auth.auth()

    def test_camera_401_forces_refresh_on_next_viewer(self):
        self.refresh()
        api = WyzeAPI("/unused", self.auth)
        with patch("protocol.urllib.request.urlopen", side_effect=urllib.error.HTTPError("test", 401, "denied", {}, None)):
            with self.assertRaises(urllib.error.HTTPError):
                api.request("/test", {})
        self.refresh("after-camera-rejection")
        self.assertEqual(self.opener.open.call_count, 2)

    def test_portal_token_is_rejected_and_refresh_is_delayed(self):
        with self.assertRaises(WebLoginRequired):
            self.refresh(access_token=token(scope=["email", "openid"]))
        with self.assertRaises(WebLoginRequired):
            self.auth.auth()
        self.assertEqual(self.opener.open.call_count, 1)

    def test_cookie_header_injection_is_rejected_before_network(self):
        self.seed.write_text("cookie\r\nother=value")
        with self.assertRaises(ValueError):
            self.auth.auth()
        self.opener.open.assert_not_called()

    def test_malformed_response_is_rejected_with_backoff(self):
        with self.assertRaises(WebLoginRequired):
            self.refresh(access_token="not-a-jwt")
        with self.assertRaises(WebLoginRequired):
            self.auth.auth()
        self.assertEqual(self.opener.open.call_count, 1)

    def test_corrupt_state_can_recover_from_seed(self):
        self.state.parent.mkdir()
        self.state.write_text("incomplete JSON")
        self.refresh()
        self.assertEqual(self.auth.auth()["user_id"], "test-user")


if __name__ == "__main__":
    unittest.main()
