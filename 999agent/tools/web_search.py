"""Web search tool for 999agent — fetches search results and page content.

Registers two tools:
  - web_search(query, n=5)  — search the web
  - fetch(url)              — fetch a page as readable text

Registration pattern: register() returns a dict of {name: {"fn": func, "description": str, "category": str}}.
"""

import re
import urllib.request
import urllib.parse
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()


def web_search_impl(query: str, n: int = 5) -> str:
    """Search the web via DuckDuckGo HTML."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "999agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []
        for m in re.finditer(
            r'<a rel="nofollow" href="(.*?)".*?>(.*?)</a>', html, re.DOTALL
        ):
            url_str = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if url_str and title and len(results) < n:
                results.append(f"• {title}\n  {url_str}")

        return "\n".join(results) if results else f"No results found for: {query}"
    except Exception as e:
        return f"Search failed: {e}"


def fetch_impl(url: str) -> str:
    """Fetch a URL and return readable text (HTML stripped)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "999agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Strip style/script tags
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
        # Strip all HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Limit to first 8000 chars
        return text[:8000] + ("..." if len(text) > 8000 else "")
    except Exception as e:
        return f"Fetch failed: {e}"


def register() -> dict:
    """Register web tools as a dict compatible with 999agent's tool loader.

    Returns: {name: {"fn": callable, "description": str, "category": str}}
    """
    return {
        "web_search": {
            "fn": web_search_impl,
            "description": "Search the web and return results",
            "category": "web",
        },
        "fetch": {
            "fn": fetch_impl,
            "description": "Fetch a URL and return readable text",
            "category": "web",
        },
    }
