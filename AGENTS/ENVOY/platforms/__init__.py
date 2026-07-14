"""⟡ ENVOY platform adapters.

Every adapter exposes exactly one write method: post(text) -> url.
There is deliberately no dm(), no follow(), no like(), no reply().
Those absences are the constitution expressed as code. Do not add them.
"""


def get_platform(name: str):
    if name == "bluesky":
        from . import bluesky
        return bluesky
    if name == "x":
        from . import x
        return x
    if name == "mastodon":
        from . import mastodon
        return mastodon
    raise ValueError(f"unknown platform '{name}'")
