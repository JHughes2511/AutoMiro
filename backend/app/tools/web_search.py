"""
Free web search via DuckDuckGo — no API key required.
"""

from duckduckgo_search import DDGS
from ..utils.logger import get_logger

logger = get_logger("tools.web_search")


def web_search(query: str, max_results: int = 8) -> list[dict]:
    """
    Search the web using DuckDuckGo.
    Returns list of {title, url, snippet} dicts.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        logger.info(f"[web_search] '{query[:60]}' → {len(results)} results")
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"[web_search] Failed: {e}")
        return []


def web_search_formatted(query: str, max_results: int = 8) -> str:
    """Returns search results as a formatted string for agent consumption."""
    results = web_search(query, max_results)
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['snippet']}")
        lines.append(f"   Source: {r['url']}\n")
    return "\n".join(lines)
