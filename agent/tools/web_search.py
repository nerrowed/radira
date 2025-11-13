"""Web search tool using multiple search providers."""

from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urlparse, quote_plus
import json

from .base import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for searching the web using multiple providers."""

    def __init__(self, max_results: int = 5):
        """Initialize web search tool.

        Args:
            max_results: Maximum number of search results to return
        """
        super().__init__()
        self.max_results = max_results

        # Try to import duckduckgo_search
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
            self.ddgs_available = True
        except ImportError:
            logger.warning(
                "duckduckgo-search not installed. "
                "Install with: pip install duckduckgo-search"
            )
            self.ddgs = None
            self.ddgs_available = False

        # Check if requests is available for fallback
        try:
            import requests
            self.requests = requests
            self.requests_available = True
        except ImportError:
            logger.warning("requests not installed for fallback search")
            self.requests = None
            self.requests_available = False

        self.available = self.ddgs_available or self.requests_available

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for information. Uses multiple methods: DuckDuckGo API, web scraping fallback, and instant answers. Returns titles, snippets, and URLs. Optimized for Indonesian queries."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Search query string",
                "required": True
            },
            "max_results": {
                "type": "integer",
                "description": f"Maximum number of results (default: {self.max_results}, max: 10)",
                "required": False
            }
        }

    @property
    def category(self) -> str:
        return "web"

    @property
    def examples(self) -> List[str]:
        return [
            "Search: {'query': 'Python FastAPI tutorial'}",
            "Search: {'query': 'latest React 18 features', 'max_results': 3}",
            "Search: {'query': 'weather in Jakarta'}",
        ]

    def _search_with_requests(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Fallback search using requests to scrape DuckDuckGo HTML.

        Args:
            query: Search query
            max_results: Max results

        Returns:
            List of result dicts
        """
        if not self.requests_available:
            return []

        try:
            # Use DuckDuckGo HTML version (lite)
            url = f"https://lite.duckduckgo.com/lite/"
            params = {
                "q": query,
                "kl": "id-id"  # Indonesia region
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = self.requests.post(url, data=params, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML using basic string parsing (avoid BeautifulSoup dependency)
            html = response.text
            results = []

            # Simple HTML parsing for DuckDuckGo lite results
            # Results are in format: <a rel="nofollow" href="URL">Title</a>
            import re

            # Find all result links
            pattern = r'<a rel="nofollow" href="([^"]+)">([^<]+)</a>'
            matches = re.findall(pattern, html)

            for i, (url, title) in enumerate(matches[:max_results], 1):
                if url and title and not url.startswith("//"):
                    # Get snippet (text after the link)
                    snippet_pattern = rf'>{re.escape(title)}</a>\s*<span class="link-text">([^<]+)</span>'
                    snippet_match = re.search(snippet_pattern, html)
                    snippet = snippet_match.group(1) if snippet_match else ""

                    results.append({
                        "title": title.strip(),
                        "snippet": snippet.strip() if snippet else "No description available",
                        "url": url.strip()
                    })

            logger.info(f"Requests fallback found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Requests fallback search failed: {e}")
            return []

    def execute(self, **kwargs) -> ToolResult:
        """Execute web search.

        Args:
            query: Search query string
            max_results: Maximum results to return

        Returns:
            ToolResult with search results
        """
        if not self.available:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="Web search not available. Install: pip install duckduckgo-search"
            )

        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", self.max_results)

        if not query:
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error="No search query provided"
            )

        # Limit max_results
        max_results = min(max_results, 10)

        try:
            logger.info(f"Searching for: {query}")
            results = []
            search_method = "unknown"

            # Try DuckDuckGo library first
            if self.ddgs_available:
                try:
                    # Try with region parameter for better results
                    results = list(self.ddgs.text(
                        query,
                        region="id-id",  # Indonesia region
                        safesearch="moderate",
                        max_results=max_results
                    ))
                    search_method = "duckduckgo_api"
                    logger.info(f"DuckDuckGo API returned {len(results)} results")
                except Exception as search_error:
                    logger.warning(f"DuckDuckGo API failed: {search_error}")
                    results = []

            # Fallback to requests-based scraping if DuckDuckGo failed
            if not results and self.requests_available:
                logger.info("Trying requests-based fallback search...")
                raw_results = self._search_with_requests(query, max_results)
                if raw_results:
                    # Convert to DuckDuckGo format
                    results = []
                    for res in raw_results:
                        results.append({
                            "title": res["title"],
                            "body": res["snippet"],
                            "href": res["url"]
                        })
                    search_method = "requests_scrape"
                    logger.info(f"Requests fallback returned {len(results)} results")

            # Try instant answers as last resort
            if not results and self.ddgs_available:
                try:
                    logger.info("Trying instant answers...")
                    answers = list(self.ddgs.answers(query))
                    if answers:
                        answer = answers[0]
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            output=f"Instant Answer: {answer.get('text', answer.get('answer', 'No answer'))}",
                            metadata={"query": query, "type": "instant_answer", "method": "duckduckgo_answers"}
                        )
                except Exception as e:
                    logger.warning(f"Instant answers failed: {e}")

            # No results from any method
            if not results:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    output="No results found. Web search may be temporarily unavailable or blocked. Try a different query or check your internet connection.",
                    metadata={"query": query, "count": 0, "method": "all_failed"}
                )

            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append({
                    "position": i,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                })

            # Create readable output
            output_text = f"Found {len(formatted_results)} results for '{query}':\n\n"
            for res in formatted_results:
                output_text += f"{res['position']}. {res['title']}\n"
                output_text += f"   {res['snippet']}\n"
                output_text += f"   URL: {res['url']}\n\n"

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=output_text.strip(),
                metadata={
                    "query": query,
                    "count": len(formatted_results),
                    "results": formatted_results,
                    "method": search_method
                }
            )

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                output=None,
                error=f"Search failed: {str(e)}"
            )

    @property
    def is_dangerous(self) -> bool:
        return False

    @property
    def requires_confirmation(self) -> bool:
        return False
