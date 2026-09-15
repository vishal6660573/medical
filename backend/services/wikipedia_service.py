import re
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.core.logs import logger


class WikipediaResult(BaseModel):
    title: str
    extract: str
    url: str


class WikipediaService:
    """
    Asynchronous Wikipedia retrieval service for fallback knowledge.
    Uses Wikipedia's official MediaWiki / REST APIs.
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        max_chars: Optional[int] = None,
        timeout: Optional[float] = None
    ):
        self.user_agent = user_agent or getattr(
            settings, "WIKIPEDIA_USER_AGENT", "SmartHealthPlatform/1.0 (medical-bot; contact@smarthealth.local)"
        )
        self.max_chars = max_chars or getattr(settings, "WIKIPEDIA_MAX_CHARS", 2500)
        self.timeout = timeout or getattr(settings, "WIKIPEDIA_TIMEOUT", 5.0)

    def _clean_query(self, query: str) -> str:
        """Strip conversational filler from query for better Wikipedia search hit rate."""
        q = query.strip()
        # Remove common question prefixes
        q = re.sub(
            r"^(what is|what are|what causes|what does|tell me about|explain|describe|define|how does|why does)\s+",
            "",
            q,
            flags=re.IGNORECASE
        )
        # Remove trailing question mark or punctuation
        q = re.sub(r"[?!.,;]+$", "", q).strip()
        return q or query.strip()

    async def search_and_summarize(self, query: str) -> Optional[WikipediaResult]:
        """
        Search Wikipedia for the query and retrieve a clean summary of the most relevant page.
        Returns WikipediaResult if found, or None if no results / error occurred.
        """
        if not getattr(settings, "WIKIPEDIA_ENABLED", True):
            logger.info("Wikipedia fallback is disabled in settings.")
            return None

        clean_term = self._clean_query(query)
        if not clean_term:
            return None

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=self.timeout, follow_redirects=True) as client:
                # 1. Search Wikipedia for matching page title
                search_url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": clean_term,
                    "format": "json",
                    "srlimit": 1,
                    "utf8": "1"
                }

                resp = await client.get(search_url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"Wikipedia search returned status {resp.status_code} for query '{clean_term}'")
                    return None

                data = resp.json()
                search_results = data.get("query", {}).get("search", [])
                if not search_results:
                    logger.info(f"No Wikipedia results found for search query: '{clean_term}'")
                    return None

                top_title = search_results[0].get("title")
                if not top_title:
                    return None

                # 2. Fetch page summary from Wikipedia REST API
                encoded_title = httpx.URL(top_title).raw_path.decode("utf-8")
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
                summary_resp = await client.get(summary_url)

                if summary_resp.status_code == 200:
                    summary_data = summary_resp.json()
                    extract = summary_data.get("extract", "").strip()
                    page_url = summary_data.get("content_urls", {}).get("desktop", {}).get(
                        "page", f"https://en.wikipedia.org/wiki/{top_title.replace(' ', '_')}"
                    )
                    page_title = summary_data.get("title", top_title)

                    if extract:
                        if len(extract) > self.max_chars:
                            extract = extract[:self.max_chars] + "..."
                        logger.info(f"Wikipedia retrieved article '{page_title}' ({len(extract)} chars)")
                        return WikipediaResult(
                            title=page_title,
                            extract=extract,
                            url=page_url
                        )

                # Fallback to extracts API if REST summary not available
                extract_params = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": "1",
                    "explaintext": "1",
                    "titles": top_title,
                    "format": "json",
                    "utf8": "1"
                }
                extract_resp = await client.get(search_url, params=extract_params)
                if extract_resp.status_code == 200:
                    pages = extract_resp.json().get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        if page_id != "-1" and "extract" in page_data:
                            extract = page_data["extract"].strip()
                            if extract:
                                if len(extract) > self.max_chars:
                                    extract = extract[:self.max_chars] + "..."
                                return WikipediaResult(
                                    title=page_data.get("title", top_title),
                                    extract=extract,
                                    url=f"https://en.wikipedia.org/wiki/{top_title.replace(' ', '_')}"
                                )

                return None

        except httpx.TimeoutException:
            logger.warning(f"Wikipedia request timed out for query '{clean_term}'")
            return None
        except Exception as e:
            logger.warning(f"Wikipedia retrieval failed gracefully for query '{clean_term}': {e}")
            return None


_wiki_instance: Optional[WikipediaService] = None


def get_wikipedia_service() -> WikipediaService:
    global _wiki_instance
    if _wiki_instance is None:
        _wiki_instance = WikipediaService()
    return _wiki_instance
