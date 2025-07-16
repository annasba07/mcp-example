import re
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import time
import hashlib

logger = logging.getLogger(__name__)

class WebUtils:
    """Utility functions for web scraping and content processing"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate if a string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
    
    @staticmethod
    def get_url_hash(url: str) -> str:
        """Generate a hash for URL deduplication"""
        return hashlib.md5(url.encode()).hexdigest()
    
    @staticmethod
    def is_pdf_url(url: str) -> bool:
        """Check if URL points to a PDF file"""
        return url.lower().endswith('.pdf') or 'pdf' in url.lower()
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text using simple frequency analysis"""
        if not text:
            return []
        
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'since', 'until',
            'while', 'where', 'when', 'why', 'what', 'which', 'who', 'how',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'only', 'own', 'same', 'than', 'too', 'very',
            'can', 'will', 'just', 'don', 'should', 'now', 'this', 'that',
            'these', 'those', 'are', 'was', 'were', 'been', 'being', 'have',
            'has', 'had', 'having', 'does', 'did', 'doing', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'will', 'can'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 1000) -> str:
        """Truncate text to maximum length with ellipsis"""
        if len(text) <= max_length:
            return text
        
        # Try to truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # If we can find a reasonable word boundary
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    @staticmethod
    def extract_meta_info(soup) -> Dict[str, Any]:
        """Extract metadata from HTML soup"""
        meta_info = {}
        
        try:
            # Title
            title_tag = soup.find('title')
            if title_tag:
                meta_info['title'] = WebUtils.clean_text(title_tag.get_text())
            
            # Meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                meta_info['description'] = WebUtils.clean_text(desc_tag.get('content', ''))
            
            # Meta keywords
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag:
                meta_info['meta_keywords'] = WebUtils.clean_text(keywords_tag.get('content', ''))
            
            # Open Graph data
            og_title = soup.find('meta', property='og:title')
            if og_title:
                meta_info['og_title'] = WebUtils.clean_text(og_title.get('content', ''))
            
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                meta_info['og_description'] = WebUtils.clean_text(og_desc.get('content', ''))
            
            # Author
            author_tag = soup.find('meta', attrs={'name': 'author'})
            if author_tag:
                meta_info['author'] = WebUtils.clean_text(author_tag.get('content', ''))
            
            # Publication date
            date_tag = soup.find('meta', attrs={'name': 'date'}) or soup.find('meta', property='article:published_time')
            if date_tag:
                meta_info['published_date'] = WebUtils.clean_text(date_tag.get('content', ''))
            
        except Exception as e:
            logger.warning(f"Error extracting meta info: {e}")
        
        return meta_info

class RateLimiter:
    """Simple rate limiter for web requests"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def can_make_request(self, domain: str) -> bool:
        """Check if we can make a request to the domain"""
        current_time = time.time()
        
        if domain not in self.requests:
            self.requests[domain] = []
        
        # Remove old requests outside time window
        self.requests[domain] = [
            req_time for req_time in self.requests[domain]
            if current_time - req_time < self.time_window
        ]
        
        # Check if we can make a new request
        if len(self.requests[domain]) < self.max_requests:
            self.requests[domain].append(current_time)
            return True
        
        return False
    
    def get_wait_time(self, domain: str) -> float:
        """Get how long to wait before next request"""
        if domain not in self.requests or not self.requests[domain]:
            return 0.0
        
        oldest_request = min(self.requests[domain])
        wait_time = self.time_window - (time.time() - oldest_request)
        return max(0.0, wait_time)

class ContentExtractor:
    """Extract main content from web pages"""
    
    @staticmethod
    def extract_main_content(soup) -> str:
        """Extract main content from HTML soup"""
        try:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try to find main content areas
            main_content = ""
            
            # Look for common content containers
            content_selectors = [
                'main',
                'article',
                '[role="main"]',
                '.content',
                '.main-content',
                '.post-content',
                '.entry-content',
                '.article-content',
                '#content',
                '#main'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    main_content = content_element.get_text(separator=' ')
                    break
            
            # If no main content found, use body
            if not main_content:
                body = soup.find('body')
                if body:
                    main_content = body.get_text(separator=' ')
            
            return WebUtils.clean_text(main_content)
            
        except Exception as e:
            logger.error(f"Error extracting main content: {e}")
            return ""
    
    @staticmethod
    def extract_links(soup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML soup"""
        links = []
        
        try:
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = WebUtils.clean_text(link.get_text())
                
                if href and text:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(base_url, href)
                    
                    if WebUtils.is_valid_url(absolute_url):
                        links.append({
                            'url': absolute_url,
                            'text': text,
                            'title': link.get('title', '')
                        })
        
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        
        return links[:50]  # Limit to 50 links