"""
⟡ Bluesky adapter. Free. No per-post cost. This is where the voice gets proven.

Credentials (in ~/AZOTH/.env):
    BLUESKY_HANDLE=you.bsky.social
    BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx     <- an APP password, never the real one
                                                    (Settings > App Passwords)
"""

import os
from datetime import datetime, timezone

import requests

API = "https://bsky.social/xrpc"


def _session() -> tuple[str, str]:
    handle = os.getenv("BLUESKY_HANDLE")
    pw = os.getenv("BLUESKY_APP_PASSWORD")
    if not (handle and pw):
        raise RuntimeError("BLUESKY_HANDLE / BLUESKY_APP_PASSWORD not set in .env")
    r = requests.post(f"{API}/com.atproto.server.createSession",
                      json={"identifier": handle, "password": pw}, timeout=20)
    r.raise_for_status()
    d = r.json()
    return d["accessJwt"], d["did"]


def post(text: str) -> str:
    jwt, did = _session()
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    r = requests.post(
        f"{API}/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {jwt}"},
        json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
        timeout=20,
    )
    r.raise_for_status()
    rkey = r.json()["uri"].rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{os.getenv('BLUESKY_HANDLE')}/post/{rkey}"


def read_timeline(limit: int = 20) -> list[dict]:
    """Free. Used by signal watch. Read only."""
    jwt, _ = _session()
    r = requests.get(f"{API}/app.bsky.feed.getTimeline",
                     headers={"Authorization": f"Bearer {jwt}"},
                     params={"limit": limit}, timeout=20)
    r.raise_for_status()
    return r.json().get("feed", [])


def search(query: str, limit: int = 25) -> list[dict]:
    """Free. Signal watch. Read only."""
    jwt, _ = _session()
    r = requests.get(f"{API}/app.bsky.feed.searchPosts",
                     headers={"Authorization": f"Bearer {jwt}"},
                     params={"q": query, "limit": limit}, timeout=20)
    r.raise_for_status()
    return r.json().get("posts", [])
