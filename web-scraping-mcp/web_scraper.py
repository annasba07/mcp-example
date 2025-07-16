import logging
import asyncio
from typing import Optional, Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time

from web_utils import WebUtils, RateLimiter, ContentExtractor

logger = logging.getLogger(__name__)

class WebScraper:
    """Main web scraping functionality"""
    
    def __init__(self, max_requests_per_domain: int = 5, timeout: int = 30):
        self.rate_limiter = RateLimiter(max_requests_per_domain, 60)
        self.timeout = timeout
        self.session = None
        
        # Common headers to appear more like a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch and process a single URL"""
        if not WebUtils.is_valid_url(url):
            return {"error": "Invalid URL format"}
        
        domain = WebUtils.extract_domain(url)
        
        # Check rate limiting
        if not self.rate_limiter.can_make_request(domain):
            wait_time = self.rate_limiter.get_wait_time(domain)
            return {"error": f"Rate limited. Wait {wait_time:.1f} seconds before retrying"}
        
        try:
            logger.info(f"Fetching URL: {url}")
            
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Handle different content types
            content_type = response.headers.get('content-type', '').lower()
            
            if 'pdf' in content_type or WebUtils.is_pdf_url(url):
                return await self._process_pdf_response(response, url)
            elif 'html' in content_type or 'text' in content_type:
                return await self._process_html_response(response, url)
            else:
                return {"error": f"Unsupported content type: {content_type}"}
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return {"error": f"HTTP error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return {"error": f"Fetch error: {str(e)}"}
    
    async def _process_html_response(self, response: httpx.Response, url: str) -> Dict[str, Any]:
        """Process HTML response"""
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            meta_info = WebUtils.extract_meta_info(soup)
            
            # Extract main content
            main_content = ContentExtractor.extract_main_content(soup)
            
            # Extract links
            links = ContentExtractor.extract_links(soup, url)
            
            # Extract keywords
            keywords = WebUtils.extract_keywords(main_content)
            
            # Calculate content stats
            word_count = len(main_content.split()) if main_content else 0
            
            result = {
                "status": "success",
                "url": url,
                "domain": WebUtils.extract_domain(url),
                "title": meta_info.get('title', ''),
                "description": meta_info.get('description', ''),
                "content": main_content,
                "content_preview": WebUtils.truncate_text(main_content, 500),
                "word_count": word_count,
                "keywords": keywords,
                "links": links,
                "metadata": meta_info,
                "fetched_at": datetime.now().isoformat(),
                "content_type": "html"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing HTML response: {e}")
            return {"error": f"HTML processing error: {str(e)}"}
    
    async def _process_pdf_response(self, response: httpx.Response, url: str) -> Dict[str, Any]:
        """Process PDF response"""
        try:
            # For now, return basic PDF info
            # Could be extended to extract text using PyPDF2 or pdfplumber
            result = {
                "status": "success",
                "url": url,
                "domain": WebUtils.extract_domain(url),
                "title": url.split('/')[-1],
                "content": "PDF content extraction not implemented yet",
                "content_preview": "PDF file detected",
                "word_count": 0,
                "keywords": [],
                "links": [],
                "metadata": {"content_type": "pdf"},
                "fetched_at": datetime.now().isoformat(),
                "content_type": "pdf",
                "file_size": len(response.content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF response: {e}")
            return {"error": f"PDF processing error: {str(e)}"}
    
    async def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search the web using DuckDuckGo (doesn't require API key)"""
        try:
            # Simple web search using DuckDuckGo
            # This is a basic implementation - could be enhanced with proper search APIs
            search_url = f"https://duckduckgo.com/html/?q={query}"
            
            response = await self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Extract search results (DuckDuckGo specific selectors)
            for result_div in soup.find_all('div', class_='result')[:max_results]:
                title_link = result_div.find('a', class_='result__a')
                snippet_div = result_div.find('div', class_='result__snippet')
                
                if title_link and snippet_div:
                    title = WebUtils.clean_text(title_link.get_text())
                    url = title_link.get('href')
                    snippet = WebUtils.clean_text(snippet_div.get_text())
                    
                    if url and title:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'domain': WebUtils.extract_domain(url)
                        })
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "total_results": len(results),
                "searched_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return {"error": f"Search error: {str(e)}"}
    
    async def batch_fetch_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple URLs concurrently with rate limiting"""
        results = []
        
        # Group URLs by domain for better rate limiting
        domain_groups = {}
        for url in urls:
            domain = WebUtils.extract_domain(url)
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(url)
        
        # Process each domain group with delays
        for domain, domain_urls in domain_groups.items():
            logger.info(f"Processing {len(domain_urls)} URLs from {domain}")
            
            for url in domain_urls:
                result = await self.fetch_url(url)
                results.append(result)
                
                # Small delay between requests to the same domain
                await asyncio.sleep(1)
        
        return results
    
    async def fetch_with_content_analysis(self, url: str) -> Dict[str, Any]:
        """Fetch URL with enhanced content analysis"""
        result = await self.fetch_url(url)
        
        if result.get('status') == 'success' and result.get('content'):
            # Enhanced analysis
            content = result['content']
            
            # Analyze content length and readability
            sentences = len(re.findall(r'[.!?]+', content))
            paragraphs = len(re.findall(r'\n\s*\n', content))
            
            # Detect content type/topic (simple heuristics)
            content_indicators = {
                'academic': ['research', 'study', 'analysis', 'methodology', 'findings'],
                'news': ['breaking', 'reported', 'according to', 'sources', 'news'],
                'technical': ['implementation', 'algorithm', 'code', 'technical', 'documentation'],
                'business': ['market', 'revenue', 'company', 'business', 'industry']
            }
            
            content_type_scores = {}
            for category, indicators in content_indicators.items():
                score = sum(1 for indicator in indicators if indicator.lower() in content.lower())
                content_type_scores[category] = score
            
            likely_content_type = max(content_type_scores, key=content_type_scores.get)
            
            # Add analysis to result
            result['content_analysis'] = {
                'sentence_count': sentences,
                'paragraph_count': paragraphs,
                'likely_content_type': likely_content_type,
                'content_type_scores': content_type_scores,
                'reading_time_minutes': max(1, result.get('word_count', 0) // 200)
            }
        
        return result