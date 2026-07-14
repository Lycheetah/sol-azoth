"""
⟡ Mastodon adapter. Free. Simple bearer token, no OAuth dance.

    STATUS: written, compiles, NOT LIVE-FIRED.

Credentials (in ~/AZOTH/.env):
    MASTODON_INSTANCE=https://mastodon.social
    MASTODON_TOKEN=              (Preferences > Development > New application)
"""

import os

import requests


def post(text: str) -> str:
    inst = os.getenv("MASTODON_INSTANCE", "https://mastodon.social").rstrip("/")
    tok = os.getenv("MASTODON_TOKEN")
    if not tok:
        raise RuntimeError("MASTODON_TOKEN not set in .env")
    r = requests.post(f"{inst}/api/v1/statuses",
                      headers={"Authorization": f"Bearer {tok}"},
                      json={"status": text}, timeout=20)
    r.raise_for_status()
    return r.json()["url"]
