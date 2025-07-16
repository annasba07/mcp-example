# Web Scraping MCP Server

A comprehensive Model Context Protocol (MCP) server for web scraping, content extraction, and research automation.

## Features

### 🔍 Web Search & Discovery
- **Web Search**: Search the web using DuckDuckGo
- **URL Content Extraction**: Extract and analyze content from any URL
- **Batch URL Processing**: Process multiple URLs efficiently
- **URL Extraction**: Extract URLs from text content

### 📊 Content Analysis
- **Enhanced Content Analysis**: Deep analysis of web content
- **Keyword Extraction**: Identify key terms and concepts
- **Content Categorization**: Classify content type (academic, news, technical, etc.)
- **Metadata Extraction**: Extract titles, descriptions, and meta information

### 🔬 Research Tools
- **Topic Research**: Comprehensive research on any topic
- **Multi-source Analysis**: Aggregate information from multiple sources
- **Content Synthesis**: Combine and analyze findings
- **Research Reports**: Generate structured research summaries

### 🛡️ Responsible Scraping
- **Rate Limiting**: Respectful request throttling per domain
- **User-Agent Rotation**: Appear as legitimate browser traffic
- **Error Handling**: Graceful handling of failed requests
- **Content Type Support**: HTML, PDF, and other formats

## Installation

### Basic Installation
```bash
cd web-scraping-mcp
pip install -r requirements.txt
```

### With Optional Features
```bash
# For enhanced search capabilities
pip install googlesearch-python duckduckgo-search

# For PDF processing
pip install PyPDF2 pdfplumber

# For advanced content extraction
pip install newspaper3k readability-lxml trafilatura

# Or install all optional dependencies
pip install -e .[all]
```

## Usage

### Starting the Server
```bash
python web_scraping_server.py
```

### With MCP Client
```bash
# From the parent directory
python client/mcp-client/client.py web-scraping-mcp/web_scraping_server.py
```

### Example Interactions

**Search the Web:**
```
Query: "Search for information about sustainable energy storage"
```

**Extract Content from URL:**
```
Query: "Get the content from https://example.com/article"
```

**Research a Topic:**
```
Query: "Research artificial intelligence in healthcare and provide a comprehensive report"
```

**Analyze Multiple URLs:**
```
Query: "Analyze content from these URLs: https://site1.com, https://site2.com, https://site3.com"
```

## Available Tools

### `search_web(query: str, max_results: int = 10)`
Search the web and return relevant results.

### `fetch_url_content(url: str)`
Fetch and extract content from a specific URL.

### `analyze_url_content(url: str)`
Fetch URL with enhanced content analysis including:
- Reading time estimation
- Content categorization
- Structural analysis
- Link extraction

### `batch_fetch_urls(urls: List[str])`
Efficiently fetch content from multiple URLs with rate limiting.

### `research_topic(topic: str, max_sources: int = 5)`
Comprehensive topic research:
- Web search for relevant sources
- Content extraction from top results
- Keyword analysis and aggregation
- Research report generation

### `extract_urls_from_text(text: str)`
Extract and validate URLs from text content.

## Content Analysis Features

### Automatic Content Categorization
- **Academic**: Research papers, studies, analyses
- **News**: News articles, reports, current events
- **Technical**: Documentation, tutorials, technical guides
- **Business**: Market reports, company information, industry analysis

### Metadata Extraction
- Page titles and descriptions
- Author information
- Publication dates
- Open Graph data
- Keywords and meta tags

### Content Processing
- Main content extraction (removes navigation, ads, etc.)
- Text cleaning and normalization
- Keyword frequency analysis
- Link extraction and categorization

## Rate Limiting & Ethics

### Respectful Scraping
- **Rate Limiting**: Maximum 5 requests per domain per minute
- **User-Agent**: Identifies as legitimate browser
- **Delays**: Automatic delays between requests
- **Error Handling**: Graceful handling of blocked requests

### Supported Content Types
- **HTML**: Full content extraction and analysis
- **PDF**: Basic processing (can be enhanced with PDF libraries)
- **Text**: Plain text processing
- **Redirects**: Automatic redirect following

## Configuration

### Rate Limiting
```python
# Adjust in WebScraper initialization
scraper = WebScraper(
    max_requests_per_domain=5,  # requests per minute
    timeout=30  # request timeout in seconds
)
```

### Content Extraction
```python
# Customize content selectors in ContentExtractor
content_selectors = [
    'main',
    'article',
    '[role="main"]',
    '.content',
    # Add custom selectors
]
```

## Research Workflow Example

**Input:** "Research sustainable energy storage technologies"

**Process:**
1. **Search**: Find relevant web sources
2. **Extract**: Get content from top sources
3. **Analyze**: Extract keywords, categorize content
4. **Synthesize**: Aggregate findings and generate report

**Output:** Comprehensive research report with:
- Key findings and concepts
- Source analysis
- Domain coverage
- Keyword frequency analysis

## Error Handling

The server provides detailed error messages for:
- Invalid URLs
- Rate limiting violations
- Network timeouts
- Content extraction failures
- Unsupported content types

## Integration with Research Agent

This MCP server is designed to work as part of a larger Research Assistant Agent:

```python
# Example integration
async def research_workflow(topic):
    # 1. Web search for sources
    search_results = await web_scraping_mcp.search_web(topic)
    
    # 2. Extract content from top sources
    content_results = await web_scraping_mcp.batch_fetch_urls(urls)
    
    # 3. Store in knowledge graph (future: Memory MCP)
    # 4. Organize files (future: Filesystem MCP)
    # 5. Version control (future: Git MCP)
```

## Performance Considerations

### Optimization Features
- **Concurrent Processing**: Multiple URLs processed in parallel
- **Smart Rate Limiting**: Per-domain request management
- **Content Caching**: Avoid re-fetching same content
- **Selective Extraction**: Focus on main content, ignore boilerplate

### Memory Management
- **Streaming**: Process large content in chunks
- **Cleanup**: Automatic cleanup of temporary data
- **Limits**: Configurable content size limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Submit a pull request

## License

This project is part of the MCP tutorial series and is available under the MIT License.

---

*This MCP server provides the foundation for intelligent web research and content analysis workflows.*