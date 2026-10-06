"""Wyze web Lake protocol. User credentials are read only at runtime."""

import base64
import hashlib
import hmac
import json
import ssl
import struct
import time
import urllib.request
from pathlib import Path


def decrypt_xxtea(ciphertext, key):
    raw = base64.b64decode(ciphertext)
    if len(raw) % 4:
        raise ValueError("Invalid encrypted credential length")
    values = list(struct.unpack("<" + "I" * (len(raw) // 4), raw))
    keys = struct.unpack("<4I", key.encode()[:16].ljust(16, b"\0"))
    n = len(values) - 1
    delta = 0x9E3779B9
    total = (6 + 52 // (n + 1)) * delta & 0xFFFFFFFF
    y = values[0]

    def mix(z, y, total, p, e):
        return (
            ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4))
            ^ ((total ^ y) + (keys[(p & 3) ^ e] ^ z))
        ) & 0xFFFFFFFF

    while total:
        e = total >> 2 & 3
        for p in range(n, 0, -1):
            z = values[p - 1]
            values[p] = (values[p] - mix(z, y, total, p, e)) & 0xFFFFFFFF
            y = values[p]
        z = values[n]
        values[0] = (values[0] - mix(z, y, total, 0, e)) & 0xFFFFFFFF
        y = values[0]
        total = (total - delta) & 0xFFFFFFFF
    packed = struct.pack("<" + "I" * len(values), *values)
    size = values[-1]
    if not len(packed) - 7 <= size <= len(packed) - 4:
        raise ValueError("Credential decryption failed")
    return packed[:size].decode("utf8")


# This signing constant ships in Wyze's public web client; it is not an account secret.
WEB_SIGNING_KEY = "gbJojEBViLklgwyyDikx5ztSvKBXI5oU"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"


def signature(body, token):
    key = hashlib.md5((token + WEB_SIGNING_KEY).encode()).hexdigest().encode()
    return hmac.new(key, body.encode(), hashlib.md5).hexdigest()


class WyzeAPI:
    def __init__(self, state_path):
        self.state_path = Path(state_path)

    def auth(self):
        data = json.loads(self.state_path.read_text())["auth"]
        if not data.get("access_token") or not data.get("user_id"):
            raise ValueError("Authentication state is incomplete")
        return data

    def request(self, path, body, core=False, auth=None):
        auth = auth or self.auth()
        body = dict(body, nonce=int(time.time() * 1000))
        serialized = json.dumps(body, separators=(",", ":"))
        host = "app-core.cloud.wyze.com" if core else "app.wyzecam.com"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": USER_AGENT,
            "access_token": auth["access_token"],
            "appid": "strv_e7f78e9e7738dc50",
            "appinfo": "wyze_web_2.3.1",
            "signature2": signature(serialized, auth["access_token"]),
            "Origin": "https://my.wyze.com",
            "Referer": "https://my.wyze.com/",
        }
        request = urllib.request.Request(
            "https://" + host + path, serialized.encode(), headers
        )
        with urllib.request.urlopen(
            request, timeout=15, context=ssl.create_default_context()
        ) as response:
            data = json.load(response)
        if str(data.get("code")) != "1":
            # API messages can contain identifiers or credentials. Log only the numeric status.
            raise RuntimeError("Wyze API status " + str(data.get("code")))
        return data["data"]

    def camera(self, name):
        data = self.request(
            "/app/v4/home/get-home-devices",
            {"device_category": "camera", "env": ""},
            core=True,
        )
        matches = [
            d
            for d in data["device_list"]
            if d.get("nickname", "").casefold() == name.casefold()
        ]
        if len(matches) != 1:
            raise ValueError("Camera name must identify exactly one device")
        camera = matches[0]
        if camera["device_model"] != "HL_PAN4":
            raise ValueError("This receiver has only been verified with Cam Pan v4")
        return {key: camera[key] for key in ("device_id", "device_model")}

    def session(self, camera, uid):
        auth = self.auth()
        streams = self.request(
            "/app/v4/camera/get-streams",
            {
                "device_list": [
                    dict(camera, provider="lake", parameters={"use_trickle": True})
                ]
            },
            auth=auth,
        )
        stream = streams[0]
        if stream["provider"] != "lake" or stream["params"]["encryption_mode"] != 7:
            raise ValueError("Unexpected camera transport or encryption mode")
        params = stream["params"]
        session = self.request(
            "/app/v4/wcsa/create-connection",
            dict(camera, mode=3, uid=uid, expire_time=3600, resolution=2),
            auth=auth,
        )
        key = decrypt_xxtea(params["encryption_key"], auth["access_token"])
        salt = base64.b64decode(
            decrypt_xxtea(params["encryption_salt"], auth["access_token"])
        )
        if len(salt) != 32:
            raise ValueError("Invalid media salt length")
        return session, params, key, salt

    def renew(self, camera, uid):
        return self.request(
            "/app/v4/wcsa/renew-token", dict(camera, uid=uid, expire_time=3600)
        )["rtc_token"]
