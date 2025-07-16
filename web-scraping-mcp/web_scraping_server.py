import logging
import asyncio
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
from pathlib import Path

from web_scraper import WebScraper
from web_utils import WebUtils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("web-scraping")

@mcp.tool()
async def search_web(query: str, max_results: int = 10) -> str:
    """Search the web for information on a given topic
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)
    """
    logger.info(f"Searching web for: {query}")
    
    try:
        async with WebScraper() as scraper:
            result = await scraper.search_web(query, max_results)
            
            if "error" in result:
                return f"Error: {result['error']}"
            
            response = f"""
Web Search Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Found {result['total_results']} results for: "{result['query']}"

Results:
"""
            
            for i, search_result in enumerate(result['results'], 1):
                response += f"""
{i}. {search_result['title']}
   URL: {search_result['url']}
   Domain: {search_result['domain']}
   Snippet: {search_result['snippet']}
   
"""
            
            response += f"Search completed at: {result['searched_at']}"
            
            return response
            
    except Exception as e:
        logger.error(f"Error in search_web: {e}")
        return f"Error searching web: {str(e)}"

@mcp.tool()
async def fetch_url_content(url: str) -> str:
    """Fetch and extract content from a specific URL
    
    Args:
        url: URL to fetch and analyze
    """
    logger.info(f"Fetching content from: {url}")
    
    try:
        async with WebScraper() as scraper:
            result = await scraper.fetch_url(url)
            
            if "error" in result:
                return f"Error: {result['error']}"
            
            response = f"""
URL Content Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully fetched content from: {result['url']}

📄 Basic Information:
├── Title: {result.get('title', 'N/A')}
├── Domain: {result.get('domain', 'N/A')}
├── Content Type: {result.get('content_type', 'N/A')}
├── Word Count: {result.get('word_count', 0)}
└── Fetched: {result.get('fetched_at', 'N/A')}

📝 Description:
{result.get('description', 'No description available')}

📊 Content Preview:
{result.get('content_preview', 'No content preview available')}

🔍 Top Keywords:
{', '.join(result.get('keywords', [])[:10])}

🔗 Links Found: {len(result.get('links', []))}
"""
            
            # Add metadata if available
            if result.get('metadata'):
                response += "\n📋 Metadata:\n"
                for key, value in result['metadata'].items():
                    if value:
                        response += f"├── {key}: {value}\n"
            
            return response
            
    except Exception as e:
        logger.error(f"Error in fetch_url_content: {e}")
        return f"Error fetching URL content: {str(e)}"

@mcp.tool()
async def analyze_url_content(url: str) -> str:
    """Fetch URL and provide enhanced content analysis
    
    Args:
        url: URL to fetch and analyze in depth
    """
    logger.info(f"Analyzing content from: {url}")
    
    try:
        async with WebScraper() as scraper:
            result = await scraper.fetch_with_content_analysis(url)
            
            if "error" in result:
                return f"Error: {result['error']}"
            
            response = f"""
Enhanced URL Content Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully analyzed content from: {result['url']}

📄 Basic Information:
├── Title: {result.get('title', 'N/A')}
├── Domain: {result.get('domain', 'N/A')}
├── Content Type: {result.get('content_type', 'N/A')}
├── Word Count: {result.get('word_count', 0)}
└── Fetched: {result.get('fetched_at', 'N/A')}

📊 Content Analysis:
"""
            
            if 'content_analysis' in result:
                analysis = result['content_analysis']
                response += f"""├── Sentences: {analysis.get('sentence_count', 0)}
├── Paragraphs: {analysis.get('paragraph_count', 0)}
├── Reading Time: ~{analysis.get('reading_time_minutes', 0)} minutes
├── Content Category: {analysis.get('likely_content_type', 'Unknown')}
└── Category Scores: {analysis.get('content_type_scores', {})}
"""
            
            response += f"""
📝 Description:
{result.get('description', 'No description available')}

🔍 Top Keywords:
{', '.join(result.get('keywords', [])[:15])}

📄 Content Summary:
{result.get('content_preview', 'No content preview available')}

🔗 Related Links ({len(result.get('links', []))}):
"""
            
            # Show top links
            for i, link in enumerate(result.get('links', [])[:5], 1):
                response += f"├── {i}. {link.get('text', 'No text')[:60]}...\n"
                response += f"│   URL: {link.get('url', 'N/A')}\n"
            
            if len(result.get('links', [])) > 5:
                response += f"└── ... and {len(result.get('links', [])) - 5} more links\n"
            
            return response
            
    except Exception as e:
        logger.error(f"Error in analyze_url_content: {e}")
        return f"Error analyzing URL content: {str(e)}"

@mcp.tool()
async def batch_fetch_urls(urls: List[str]) -> str:
    """Fetch content from multiple URLs efficiently
    
    Args:
        urls: List of URLs to fetch
    """
    logger.info(f"Batch fetching {len(urls)} URLs")
    
    try:
        async with WebScraper() as scraper:
            results = await scraper.batch_fetch_urls(urls)
            
            successful_results = [r for r in results if r.get('status') == 'success']
            failed_results = [r for r in results if 'error' in r]
            
            response = f"""
Batch URL Fetch Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
├── Total URLs: {len(urls)}
├── Successful: {len(successful_results)}
├── Failed: {len(failed_results)}
└── Success Rate: {len(successful_results)/len(urls)*100:.1f}%

✅ Successful Results:
"""
            
            for i, result in enumerate(successful_results, 1):
                response += f"""
{i}. {result.get('title', 'Untitled')}
   URL: {result.get('url', 'N/A')}
   Domain: {result.get('domain', 'N/A')}
   Words: {result.get('word_count', 0)}
   Keywords: {', '.join(result.get('keywords', [])[:5])}
   
"""
            
            if failed_results:
                response += "❌ Failed Results:\n"
                for i, result in enumerate(failed_results, 1):
                    response += f"{i}. Error: {result.get('error', 'Unknown error')}\n"
            
            return response
            
    except Exception as e:
        logger.error(f"Error in batch_fetch_urls: {e}")
        return f"Error in batch fetch: {str(e)}"

@mcp.tool()
async def research_topic(topic: str, max_sources: int = 5) -> str:
    """Research a topic by searching and analyzing multiple sources
    
    Args:
        topic: Research topic to investigate
        max_sources: Maximum number of sources to analyze (default: 5)
    """
    logger.info(f"Researching topic: {topic}")
    
    try:
        async with WebScraper() as scraper:
            # Step 1: Search for the topic
            search_result = await scraper.search_web(topic, max_sources * 2)
            
            if "error" in search_result:
                return f"Error: {search_result['error']}"
            
            # Step 2: Fetch content from top results
            top_urls = [r['url'] for r in search_result['results'][:max_sources]]
            content_results = await scraper.batch_fetch_urls(top_urls)
            
            # Step 3: Analyze and compile research
            successful_results = [r for r in content_results if r.get('status') == 'success']
            
            # Aggregate keywords and content
            all_keywords = []
            total_words = 0
            domains = set()
            
            for result in successful_results:
                all_keywords.extend(result.get('keywords', []))
                total_words += result.get('word_count', 0)
                domains.add(result.get('domain', ''))
            
            # Count keyword frequency
            keyword_freq = {}
            for keyword in all_keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            response = f"""
Research Report: {topic}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Research Summary:
├── Topic: {topic}
├── Sources Analyzed: {len(successful_results)}
├── Total Words: {total_words:,}
├── Domains Covered: {len(domains)}
└── Research Date: {search_result.get('searched_at', 'N/A')}

🔍 Key Findings (Top Keywords):
"""
            
            for keyword, count in top_keywords:
                response += f"├── {keyword}: {count} mentions\n"
            
            response += f"\n📚 Sources Analyzed:\n"
            
            for i, result in enumerate(successful_results, 1):
                response += f"""
{i}. {result.get('title', 'Untitled')}
   URL: {result.get('url', 'N/A')}
   Domain: {result.get('domain', 'N/A')}
   Words: {result.get('word_count', 0)}
   Preview: {result.get('content_preview', 'No preview')[:100]}...
   
"""
            
            response += f"\n🌐 Domains Covered:\n"
            for domain in sorted(domains):
                response += f"├── {domain}\n"
            
            return response
            
    except Exception as e:
        logger.error(f"Error in research_topic: {e}")
        return f"Error researching topic: {str(e)}"

@mcp.tool()
async def extract_urls_from_text(text: str) -> str:
    """Extract and validate URLs from text content
    
    Args:
        text: Text content to extract URLs from
    """
    logger.info("Extracting URLs from text")
    
    try:
        import re
        
        # URL regex pattern
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?)]'
        
        # Find all URLs
        urls = re.findall(url_pattern, text)
        
        # Validate and categorize URLs
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            if WebUtils.is_valid_url(url):
                valid_urls.append({
                    'url': url,
                    'domain': WebUtils.extract_domain(url),
                    'is_pdf': WebUtils.is_pdf_url(url)
                })
            else:
                invalid_urls.append(url)
        
        # Group by domain
        domain_groups = {}
        for url_info in valid_urls:
            domain = url_info['domain']
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(url_info)
        
        response = f"""
URL Extraction Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Summary:
├── Total URLs Found: {len(urls)}
├── Valid URLs: {len(valid_urls)}
├── Invalid URLs: {len(invalid_urls)}
├── Unique Domains: {len(domain_groups)}
└── PDF Files: {sum(1 for u in valid_urls if u['is_pdf'])}

🌐 URLs by Domain:
"""
        
        for domain, domain_urls in domain_groups.items():
            response += f"\n{domain} ({len(domain_urls)} URLs):\n"
            for url_info in domain_urls[:5]:  # Show first 5 URLs per domain
                pdf_indicator = " [PDF]" if url_info['is_pdf'] else ""
                response += f"├── {url_info['url']}{pdf_indicator}\n"
            
            if len(domain_urls) > 5:
                response += f"└── ... and {len(domain_urls) - 5} more URLs\n"
        
        if invalid_urls:
            response += f"\n❌ Invalid URLs:\n"
            for invalid_url in invalid_urls:
                response += f"├── {invalid_url}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in extract_urls_from_text: {e}")
        return f"Error extracting URLs: {str(e)}"

def main():
    """Main function to run the web scraping MCP server"""
    logger.info("Starting Web Scraping MCP Server...")
    
    # Log available features
    logger.info("✓ Web search available")
    logger.info("✓ URL content extraction available")
    logger.info("✓ Batch URL processing available")
    logger.info("✓ Content analysis available")
    logger.info("✓ Research topic compilation available")
    
    # Check optional dependencies
    try:
        import PyPDF2
        logger.info("✓ PDF processing available")
    except ImportError:
        logger.warning("✗ PDF processing not available (install with: pip install PyPDF2)")
    
    try:
        import newspaper
        logger.info("✓ Advanced article extraction available")
    except ImportError:
        logger.warning("✗ Advanced article extraction not available (install with: pip install newspaper3k)")
    
    # Run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()