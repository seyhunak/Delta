from __future__ import annotations

import httpx

from dp.providers.base import ProviderError


class TavilyClient:
    def __init__(self, api_key: str, timeout_s: float = 20.0) -> None:
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.base_url = "https://api.tavily.com"

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        payload = {
            "query": query,
            "search_depth": "basic",
            "max_results": max(1, min(max_results, 10)),
            "include_answer": False,
            "include_raw_content": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.post(f"{self.base_url}/search", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Tavily search failed: {exc}") from exc

        results = data.get("results", [])
        parsed: list[dict[str, str]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            parsed.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "url": str(item.get("url", "")).strip(),
                    "content": str(item.get("content", "")).strip(),
                }
            )
        return parsed


def build_web_context_block(results: list[dict[str, str]]) -> str:
    if not results:
        return ""

    lines = ["Web Context (Tavily):"]
    for idx, item in enumerate(results, start=1):
        title = item.get("title", "Untitled") or "Untitled"
        url = item.get("url", "")
        content = item.get("content", "")
        lines.append(f"[{idx}] {title}")
        if url:
            lines.append(f"URL: {url}")
        if content:
            lines.append(f"Snippet: {content}")
        lines.append("")

    return "\n".join(lines).strip()
