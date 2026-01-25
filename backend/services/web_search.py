"""
Web search service for gathering network outage information using real search APIs
"""
import json
import asyncio
import aiohttp
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from utils.logger import logger


class WebSearcher:
    """
    Performs web searches for network outage information using DuckDuckGo
    """
    
    @staticmethod
    def _get_headers() -> dict:
        """Get headers for web requests"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    @staticmethod
    async def _search_duckduckgo(query: str, num_results: int = 4) -> List[Dict[str, str]]:
        """
        Search using DuckDuckGo HTML scraping (no API key required)
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
        
        Returns:
            List of search results with title, snippet, url
        """
        logger.info(f"🔍 DuckDuckGo search: '{query}'")
        
        try:
            # Create SSL context that doesn't verify certificates
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                # DuckDuckGo HTML search endpoint
                url = "https://html.duckduckgo.com/html/"
                data = {"q": query}
                
                async with session.post(
                    url, 
                    data=data, 
                    headers=WebSearcher._get_headers(), 
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.error(f"DuckDuckGo search failed: {response.status}")
                        return []
                    
                    html = await response.text()
                    results = WebSearcher._parse_duckduckgo_html(html, num_results)
                    logger.info(f"📄 DuckDuckGo returned {len(results)} results")
                    return results
                    
        except asyncio.TimeoutError:
            logger.error("DuckDuckGo search timeout")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    @staticmethod
    def _parse_duckduckgo_html(html: str, max_results: int) -> List[Dict[str, str]]:
        """
        Parse DuckDuckGo HTML results
        
        Args:
            html: HTML response from DuckDuckGo
            max_results: Maximum results to extract
        
        Returns:
            List of parsed search results
        """
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all result divs
        result_divs = soup.find_all('div', class_='result')[:max_results]
        
        for div in result_divs:
            try:
                # Extract title and URL
                title_tag = div.find('a', class_='result__a')
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                url = title_tag.get('href', '')
                
                # Extract snippet
                snippet_tag = div.find('a', class_='result__snippet')
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                
                if title and url:
                    results.append({
                        "title": title,
                        "snippet": snippet,
                        "url": url,
                        "date": datetime.now().isoformat(),
                        "source": "DuckDuckGo"
                    })
            except Exception as e:
                logger.debug(f"Error parsing DuckDuckGo result: {e}")
                continue
        
        return results
    
    @staticmethod
    async def search(query: str, num_results: int = 4) -> List[Dict[str, str]]:
        """
        Search the web for network outage information
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
        
        Returns:
            List of search results with title, snippet, url, date
        """
        logger.info(f"🔍 Searching web: '{query}'")
        
        # Search DuckDuckGo
        results = await WebSearcher._search_duckduckgo(query, num_results)
        
        logger.info(f"📄 Found {len(results)} results for '{query[:30]}...'")
        return results
    
    @staticmethod
    async def search_multiple(queries: List[str], num_results: int = 4) -> List[Dict[str, str]]:
        """
        Execute multiple searches in parallel
        
        Args:
            queries: List of search query strings
            num_results: Maximum results per query
        
        Returns:
            Flattened list of all search results
        """
        logger.info(f"🔍 Executing {len(queries)} parallel searches...")
        
        # Execute all searches concurrently
        tasks = [WebSearcher.search(query, num_results) for query in queries]
        results = await asyncio.gather(*tasks)
        
        # Flatten and deduplicate results by URL
        seen_urls = set()
        all_results = []
        
        for result_set in results:
            for result in result_set:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)
        
        logger.info(f"📊 Total results collected: {len(all_results)}")

        with open("web_search.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        return all_results