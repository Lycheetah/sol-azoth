"""
⟡ X adapter. METERED. $0.015 a plain post, $0.20 if it contains a link.

    STATUS: written, compiles, NOT LIVE-FIRED. No X credentials exist yet.
    Register: verified against X's Feb 2026 pay-per-use pricing (WebSearch,
    2026-07-09). The OAuth1 signing below is unproven against the live API.
    First real call is an experiment, not a certainty. Treat it as such.

Credentials (in ~/AZOTH/.env), from an X developer app with Read+Write:
    X_API_KEY=            X_API_SECRET=
    X_ACCESS_TOKEN=       X_ACCESS_SECRET=

OAuth 1.0a is signed by hand here so ENVOY takes no new dependency.
For a JSON body the signature base string covers only the oauth_* params,
which is why the body is absent from the calculation below.
"""

import base64
import hashlib
import hmac
import os
import secrets
import time
from urllib.parse import quote

import requests

ENDPOINT = "https://api.x.com/2/tweets"


def _pct(s: str) -> str:
    return quote(str(s), safe="~")


def _auth_header(method: str, url: str) -> str:
    ck, cs = os.getenv("X_API_KEY"), os.getenv("X_API_SECRET")
    tk, ts = os.getenv("X_ACCESS_TOKEN"), os.getenv("X_ACCESS_SECRET")
    if not all((ck, cs, tk, ts)):
        raise RuntimeError("X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_SECRET not set")

    oauth = {
        "oauth_consumer_key": ck,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": tk,
        "oauth_version": "1.0",
    }
    norm = "&".join(f"{_pct(k)}={_pct(oauth[k])}" for k in sorted(oauth))
    base = f"{method.upper()}&{_pct(url)}&{_pct(norm)}"
    key = f"{_pct(cs)}&{_pct(ts)}".encode()
    oauth["oauth_signature"] = base64.b64encode(
        hmac.new(key, base.encode(), hashlib.sha1).digest()
    ).decode()
    return "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))


def post(text: str) -> str:
    # Belt and braces. envoy.py's linter already rejects links, but a $0.20
    # charge is worth refusing twice.
    if "http://" in text or "https://" in text:
        raise RuntimeError("link in post. 13x the cost, and the rooms hate it. Refused.")

    r = requests.post(
        ENDPOINT,
        headers={"Authorization": _auth_header("POST", ENDPOINT),
                 "Content-Type": "application/json"},
        json={"text": text},
        timeout=20,
    )
    r.raise_for_status()
    return f"https://x.com/i/status/{r.json()['data']['id']}"
