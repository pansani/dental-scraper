# Scrapy Best Practices

Compiled from official Scrapy documentation and community resources.

## Table of Contents

1. [Testing](#testing)
2. [Spider Architecture](#spider-architecture)
3. [Dynamic Content](#dynamic-content)
   - [API Endpoint Discovery](#5-api-endpoint-discovery-pricestock-apis)
4. [Item Loaders](#item-loaders)
5. [Data Persistence](#data-persistence)
6. [Anti-Bot Measures](#anti-bot-measures)
7. [Incremental Crawling](#incremental-crawling)
8. [Error Handling](#error-handling)
9. [Performance](#performance)

---

## Testing

Testing spiders can get particularly annoying and while nothing prevents you from writing unit tests, the task gets cumbersome quickly. Scrapy offers multiple approaches.

### 1. Spider Contracts (Built-in, Quick)

Contracts allow you to test each callback by hardcoding a sample URL and checking constraints. Each contract is prefixed with `@` in the docstring.

```python
def parse_product(self, response):
    """
    @url https://www.example.com/product/123.html
    @returns items 1
    @scrapes raw_name price external_id supplier
    """
    loader = ProductLoader(response=response)
    # ... extraction code
    yield loader.load_item()
```

**Built-in Contracts:**

| Contract | Description | Example |
|----------|-------------|---------|
| `@url` | Sample URL (mandatory) | `@url https://example.com/page` |
| `@returns` | Expected items/requests count | `@returns items 1 5` (min 1, max 5) |
| `@scrapes` | Required fields in items | `@scrapes name price sku` |
| `@cb_kwargs` | Callback keyword args (JSON) | `@cb_kwargs {"category": "shoes"}` |
| `@meta` | Request metadata (JSON) | `@meta {"playwright": true}` |

**Run contracts:**
```bash
scrapy check                    # Check all spiders
scrapy check spider_name        # Check specific spider
```

**Detect check runs in code:**
```python
import os
if os.environ.get('SCRAPY_CHECK') == 'true':
    # Running in check mode
    pass
```

### 2. Pytest with Fake Responses (Unit Tests)

Save HTML fixtures and test without network calls.

**Create test fixtures:**
```bash
mkdir -p tests/fixtures
curl -o tests/fixtures/product.html "https://example.com/product/123"
```

**Write tests:**
```python
# tests/test_spider.py
import pytest
from scrapy.http import HtmlResponse, Request
from myproject.spiders.myspider import MySpider

def fake_response(file_path, url="http://example.com"):
    """Create a fake response from a local HTML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        body = f.read()
    request = Request(url=url)
    return HtmlResponse(url=url, body=body, encoding='utf-8', request=request)

class TestMySpider:
    def setup_method(self):
        self.spider = MySpider()

    def test_parse_product_extracts_name(self):
        response = fake_response('tests/fixtures/product.html')
        items = list(self.spider.parse_product(response))

        assert len(items) == 1
        assert items[0]['raw_name'] is not None
        assert items[0]['raw_name'] != ''

    def test_parse_product_extracts_price(self):
        response = fake_response('tests/fixtures/product.html')
        items = list(self.spider.parse_product(response))

        assert items[0]['price'] is not None
        assert items[0]['price'] > 0

    def test_parse_product_extracts_sku(self):
        response = fake_response('tests/fixtures/product.html')
        items = list(self.spider.parse_product(response))

        assert items[0]['external_id'] is not None
```

**Run tests:**
```bash
pytest tests/test_spider.py -v
```

### 3. scrapy-mock (Record & Replay)

Pytest plugin that records real responses as fixtures.

```bash
pip install scrapy-mock
```

```python
# conftest.py
pytest_plugins = ['scrapy_mock']

# test_spider.py
def test_parse_product(mock_response):
    # First run: records real response
    # Subsequent runs: uses cached response
    response = mock_response('https://example.com/product/123')
    items = list(spider.parse_product(response))
    assert len(items) == 1
```

### 4. Integration Testing with CrawlerRunner

Test the full crawl process:

```python
import pytest
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import defer

@pytest.fixture
def crawler_runner():
    settings = get_project_settings()
    settings.set('CLOSESPIDER_ITEMCOUNT', 5)
    return CrawlerRunner(settings)

@defer.inlineCallbacks
def test_spider_crawls_successfully(crawler_runner):
    from myproject.spiders.myspider import MySpider

    results = []

    def collect_item(item, response, spider):
        results.append(item)

    crawler = crawler_runner.create_crawler(MySpider)
    crawler.signals.connect(collect_item, signal=signals.item_scraped)

    yield crawler_runner.crawl(crawler)

    assert len(results) > 0
```

### 5. Testing ItemLoaders Directly

```python
from scrapy.http import HtmlResponse
from myproject.loaders import ProductLoader

def test_loader_cleans_price():
    html = '<div class="price">R$ 49,90</div>'
    response = HtmlResponse(url='http://example.com', body=html, encoding='utf-8')

    loader = ProductLoader(response=response)
    loader.add_css('price', '.price::text')
    item = loader.load_item()

    assert item['price'] == 49.90

def test_loader_extracts_quantity():
    html = '<h2>Embalagem com 100 unidades</h2>'
    response = HtmlResponse(url='http://example.com', body=html, encoding='utf-8')

    loader = ProductLoader(response=response)
    loader.add_css('raw_quantity', 'h2::text')
    item = loader.load_item()

    assert item['raw_quantity'] == 100
```

### Quick Testing Commands

```bash
# Test with limited items (fastest feedback)
scrapy crawl myspider -s CLOSESPIDER_ITEMCOUNT=3 -s DOWNLOAD_DELAY=0.5

# Test single URL with shell
scrapy shell "https://example.com/product/123"

# Check contracts
scrapy check myspider

# Run pytest
pytest tests/ -v

# Run specific test
pytest tests/test_spider.py::test_parse_product -v
```

---

## Spider Architecture

### Spider Types

| Spider Type | Use Case |
|-------------|----------|
| `Spider` | Simple scraping, manual control over requests |
| `CrawlSpider` | Systematic link following with Rules |
| `XMLFeedSpider` | Parsing XML feeds |
| `CSVFeedSpider` | Parsing CSV feeds |
| `SitemapSpider` | Following sitemap.xml |

### CrawlSpider vs Regular Spider

**Use CrawlSpider when:**
- Following links across multiple pages based on patterns
- Applying different callbacks to different URL types
- Implementing complex crawling logic with minimal code

**Use Regular Spider when:**
- Single-page scraping
- Custom request generation logic
- Scenarios where link-following rules would be overly complex

### CrawlSpider Rules

```python
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class MySpider(CrawlSpider):
    name = "example"

    rules = (
        # Extract product links, call parse_product
        Rule(
            LinkExtractor(allow=r"/product/\d+"),
            callback="parse_product",
            follow=False,
            process_request="add_meta",
            errback="handle_error",
        ),
        # Follow pagination links
        Rule(
            LinkExtractor(allow=r"\?page=\d+"),
            follow=True,
        ),
    )
```

**Important:** You must explicitly set callbacks for new requests when writing CrawlSpider-based spiders; unexpected behaviour can occur otherwise.

### Selectors: XPath vs CSS

| Type | Pros | Cons |
|------|------|------|
| **XPath** | More powerful, can navigate entire DOM, query by text content | More verbose |
| **CSS** | Simpler syntax, faster for basic queries | Limited compared to XPath |

**Recommendation:** Use CSS for simple selections, XPath for complex queries.

---

## Dynamic Content

Source: [Scrapy - Selecting dynamically-loaded content](https://docs.scrapy.org/en/latest/topics/dynamic-content.html)

When webpages require JavaScript to display data, Scrapy selectors won't work on the initial HTML. Follow this priority order:

### 1. Find the Data Source (Recommended)

Before using a headless browser, investigate whether the content is already in the HTML:

**Check for embedded data:**
- Hidden inputs: `response.css("#productImage::attr(value)").get()`
- Data attributes: `response.css("[data-product-id]::attr(data-image)").get()`
- Script tags with JSON: `response.css("script::text").re_first(r'var data = ({.*?});')`

**Use browser DevTools:**
```bash
# Fetch raw HTML to inspect
scrapy fetch --nolog https://example.com > response.html
```

### 2. Extract from JavaScript

When data is in `<script>` tags, extract it directly:

**Using regex:**
```python
import json
import re

pattern = r"\bvar\s+data\s*=\s*(\{.*?\})\s*;\s*\n"
json_data = response.css("script::text").re_first(pattern)
data = json.loads(json_data)
```

**Using chompjs (for unquoted JS objects):**
```python
import chompjs

javascript = response.css("script::text").get()
data = chompjs.parse_js_object(javascript)
```

**Using js2xml:**
```python
import js2xml
from parsel import Selector

javascript = response.css("script::text").get()
xml = lxml.etree.tostring(js2xml.parse(javascript), encoding="unicode")
selector = Selector(text=xml)
selector.css('var[name="data"]').get()
```

### 3. Reproduce HTTP Requests

If data comes from an API endpoint:

1. Use browser DevTools Network tab to identify the request
2. Copy request as cURL
3. Use `Request.from_curl()` to replicate:

```python
from scrapy import Request

curl_command = '''curl 'https://api.example.com/products' -H 'Authorization: Bearer token' '''
yield Request.from_curl(curl_command, callback=self.parse_api)
```

### 4. Headless Browser (Last Resort)

Use `scrapy-playwright` only when reproduction is impossible:

```python
yield Request(
    url="https://example.com",
    meta={"playwright": True},
    callback=self.parse,
)
```

**Why avoid headless browsers:**
- Slower execution
- Higher resource consumption
- More complex debugging
- Rate limiting issues

### Real Example: Product Gallery Images

Instead of waiting for JavaScript to render a gallery:

```python
def _load_image(self, loader, response):
    # Priority 1: Hidden input (data source)
    hidden_input = response.css("#yv-productImage::attr(value)").get()
    if hidden_input and 'cdn.example.com' in hidden_input:
        loader.add_value("image_url", hidden_input)
        return

    # Priority 2: Data attribute on gallery container
    gallery_href = response.css(".gallery__frame::attr(href)").get()
    if gallery_href and 'cdn.example.com' in gallery_href:
        loader.add_value("image_url", gallery_href)
        return

    # Priority 3: Fallback to img src
    all_images = response.css("img::attr(src)").getall()
    for img in all_images:
        if img and 'cdn.example.com' in img and '/produtos/' in img:
            loader.add_value("image_url", img)
            return
```

### 5. API Endpoint Discovery (Price/Stock APIs)

Some websites load prices, stock status, or other data via internal APIs after the initial page load. Instead of waiting for JavaScript, discover and call these APIs directly.

**How to discover API endpoints:**

1. Open browser DevTools > Network tab
2. Filter by XHR/Fetch requests
3. Load the product page and watch for API calls
4. Look for endpoints like `/rest/`, `/api/`, `/ajax/`

**Real Example: Dental Speed Price API**

The price on product pages is loaded via:
```
GET /rest/V2/hsb_catalog/price?sku={SKU}
Authorization: Bearer {token}
```

Response:
```json
[{"SKU123":{"main":{"price":28.63,"special_price":27.58,"percent_discount":7}}}]
```

**Implementation pattern:**

```python
class MySpider(CrawlSpider):
    PRICE_API_URL = "https://example.com/rest/V2/catalog/price"
    PRICE_API_TOKEN = "static_token_from_page"  # Found in window.config.token

    def parse_product(self, response):
        loader = ProductLoader(response=response)
        # ... extract other data ...

        item = loader.load_item()
        sku = item.get("external_id")

        # If no price found in HTML, call the price API
        if not item.get("price") and sku:
            yield Request(
                url=f"{self.PRICE_API_URL}?sku={sku}",
                callback=self.parse_price_api,
                meta={
                    "item": item,
                    "playwright": False,  # No need for browser
                    "dont_obey_robotstxt": True,  # API often blocked by robots.txt
                },
                headers={
                    "Authorization": f"Bearer {self.PRICE_API_TOKEN}",
                    "Referer": response.url,
                    "Accept": "application/json",
                },
                errback=self.handle_price_error,
                dont_filter=True,
            )
        else:
            yield item

    def parse_price_api(self, response):
        item = response.meta["item"]
        sku = item.get("external_id")

        try:
            data = json.loads(response.text)
            if isinstance(data, list) and len(data) > 0:
                price_data = data[0].get(sku, {}).get("main", {})
                price = price_data.get("special_price") or price_data.get("price")
                if price:
                    item["price"] = float(price)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        yield item

    def handle_price_error(self, failure):
        item = failure.request.meta.get("item")
        if item:
            yield item  # Yield without price rather than losing the item
```

**Finding the API token:**

Tokens are often embedded in the page JavaScript:
```python
# In browser console
window.hsb.token  // or similar global variable

# Via Scrapy, extract from script tags:
token = response.css("script::text").re_first(r'"token"\s*:\s*"([^"]+)"')
```

**Bypassing robots.txt for specific requests:**

API endpoints are often blocked by robots.txt. Use `dont_obey_robotstxt` in request meta:

```python
yield Request(
    url=api_url,
    meta={"dont_obey_robotstxt": True},  # Bypass for this request only
    ...
)
```

This respects robots.txt for regular pages while allowing API access.

---

## Item Loaders

Item Loaders provide a flexible mechanism for populating scraped items with automatic data processing.

### Why Use Item Loaders

1. **Automated Processing**: Apply input/output processors automatically
2. **Multiple Value Collection**: Extract same field from multiple locations
3. **Reusable Processors**: Share processing logic across spiders
4. **Cleaner Code**: Separate extraction from processing

### Basic Structure

```python
from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Compose

class ProductLoader(ItemLoader):
    default_output_processor = TakeFirst()

    # Input processors - applied when adding data
    price_in = MapCompose(str.strip, parse_price)
    name_in = MapCompose(str.strip)

    # Output processors - applied when loading item
    tags_out = Compose(set, list)  # Remove duplicates
```

### Processor Types

| Processor | Description |
|-----------|-------------|
| `TakeFirst()` | Returns first non-null value |
| `MapCompose(fn1, fn2)` | Apply functions in sequence to each value |
| `Compose(fn1, fn2)` | Apply functions to entire list of values |
| `Identity()` | Return values unchanged |
| `Join(separator)` | Join values with separator |

### Usage in Spider

```python
def parse_product(self, response):
    loader = ProductLoader(item=ProductItem(), response=response)

    loader.add_css("name", "h1::text")
    loader.add_xpath("price", "//span[@class='price']/text()")
    loader.add_value("url", response.url)

    yield loader.load_item()
```

### Nested Loaders

For subsections, use nested loaders to reduce repetitive selectors:

```python
loader = ProductLoader(response=response)
details_loader = loader.nested_css("div.details")
details_loader.add_css("sku", ".sku::text")
details_loader.add_css("brand", ".brand::text")
```

---

## Data Persistence

### The Problem with FEEDS

```python
# settings.py - saves only AFTER full scrape completes
FEEDS = {
    "output/%(name)s.json": {"format": "json"},
}
```

**Issue:** If scrape is interrupted, all data is lost.

### Recommended: Database Pipeline

Each item is saved **immediately** via `process_item()`:

```python
import sqlite3

class SQLitePipeline:
    def open_spider(self, spider):
        self.connection = sqlite3.connect("products.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                external_id TEXT UNIQUE,
                name TEXT,
                price REAL,
                scraped_at TEXT
            )
        """)

    def process_item(self, item, spider):
        self.cursor.execute("""
            INSERT OR REPLACE INTO products
            (external_id, name, price, scraped_at)
            VALUES (?, ?, ?, ?)
        """, (
            item.get("external_id"),
            item.get("name"),
            item.get("price"),
            item.get("scraped_at"),
        ))
        self.connection.commit()
        return item

    def close_spider(self, spider):
        self.connection.close()
```

### Pipeline with Deduplication

```python
class NoDuplicatesPipeline:
    def open_spider(self, spider):
        self.connection = sqlite3.connect("products.db")
        self.cursor = self.connection.cursor()
        self.seen_ids = set()

        # Load existing IDs
        self.cursor.execute("SELECT external_id FROM products")
        self.seen_ids = {row[0] for row in self.cursor.fetchall()}

    def process_item(self, item, spider):
        external_id = item.get("external_id")

        if external_id in self.seen_ids:
            # Update existing record
            self.cursor.execute("""
                UPDATE products SET price = ?, scraped_at = ?
                WHERE external_id = ?
            """, (item.get("price"), item.get("scraped_at"), external_id))
        else:
            # Insert new record
            self.cursor.execute("""
                INSERT INTO products (external_id, name, price, scraped_at)
                VALUES (?, ?, ?, ?)
            """, (...))
            self.seen_ids.add(external_id)

        self.connection.commit()
        return item
```

### Batch Commits (Performance)

```python
class BatchSQLitePipeline:
    BATCH_SIZE = 100

    def open_spider(self, spider):
        self.connection = sqlite3.connect("products.db")
        self.buffer = []

    def process_item(self, item, spider):
        self.buffer.append(dict(item))

        if len(self.buffer) >= self.BATCH_SIZE:
            self._flush()

        return item

    def close_spider(self, spider):
        self._flush()  # Save remaining items
        self.connection.close()

    def _flush(self):
        if not self.buffer:
            return
        self.cursor.executemany("""
            INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)
        """, [(i["external_id"], i["name"], i["price"], i["scraped_at"])
              for i in self.buffer])
        self.connection.commit()
        self.buffer = []
```

### Pipeline Order

```python
# settings.py
ITEM_PIPELINES = {
    "myproject.pipelines.CleanerPipeline": 100,      # First: clean data
    "myproject.pipelines.ValidatorPipeline": 200,    # Second: validate
    "myproject.pipelines.DuplicatesPipeline": 300,   # Third: check dupes
    "myproject.pipelines.DatabasePipeline": 400,     # Last: save to DB
}
```

Lower numbers execute first (0-1000 range).

---

## Anti-Bot Measures

### User-Agent Rotation

```python
# middlewares.py
from fake_useragent import UserAgent

class RandomUserAgentMiddleware:
    def __init__(self):
        self.ua = UserAgent()

    def process_request(self, request, spider):
        request.headers["User-Agent"] = self.ua.random
```

### Request Delays

```python
# settings.py
DOWNLOAD_DELAY = 3  # 3 seconds between requests
RANDOMIZE_DOWNLOAD_DELAY = True  # Random delay 0.5x to 1.5x
CONCURRENT_REQUESTS_PER_DOMAIN = 2
```

### Cookies

```python
# settings.py
COOKIES_ENABLED = False  # Disable to avoid tracking
# or
COOKIES_ENABLED = True  # Enable for session-based sites
```

### Proxy Rotation

```python
class ProxyMiddleware:
    def __init__(self, proxy_list):
        self.proxies = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist("PROXY_LIST"))

    def process_request(self, request, spider):
        request.meta["proxy"] = random.choice(self.proxies)
```

### robots.txt

```python
# settings.py
ROBOTSTXT_OBEY = True  # Respect robots.txt (recommended)
```

### Best Practices Summary

1. Rotate user agents from browser pools
2. Set download delays (2+ seconds)
3. Use random delays
4. Limit concurrent requests per domain
5. Consider proxy rotation for large scrapes
6. Scrape during off-peak hours
7. Respect robots.txt

---

## Incremental Crawling

### JOBDIR - Resume Interrupted Crawls

```python
# settings.py
JOBDIR = "crawls/dental_speed"
```

Or via command line:
```bash
scrapy crawl myspider -s JOBDIR=crawls/myspider-1
```

This saves:
- Request queue
- Fingerprints of visited URLs
- Spider state

### DeltaFetch - Skip Already Scraped URLs

```bash
pip install scrapy-deltafetch
```

```python
# settings.py
SPIDER_MIDDLEWARES = {
    "scrapy_deltafetch.DeltaFetch": 100,
}
DELTAFETCH_ENABLED = True
DELTAFETCH_DIR = "deltafetch"
```

**How it works:**
1. For each Item, computes request fingerprint and stores it
2. For each Request, checks if fingerprint exists and skips if so

### Custom Deduplication

```python
class DeduplicationMiddleware:
    def __init__(self):
        self.seen_urls = set()

    def process_request(self, request, spider):
        if request.url in self.seen_urls:
            raise IgnoreRequest(f"Duplicate: {request.url}")
        self.seen_urls.add(request.url)
```

---

## Error Handling

### Using errback

```python
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError

class MySpider(Spider):
    def start_requests(self):
        yield Request(
            url="https://example.com",
            callback=self.parse,
            errback=self.handle_error,
        )

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.request.url}")

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"HTTP {response.status}: {response.url}")

        elif failure.check(DNSLookupError):
            self.logger.error(f"DNS lookup failed: {failure.request.url}")

        elif failure.check(TimeoutError):
            self.logger.error(f"Timeout: {failure.request.url}")
```

### Retry Middleware

```python
# settings.py
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
```

### Handling Specific HTTP Codes

```python
# settings.py
HTTPERROR_ALLOWED_CODES = [404, 403]  # Don't treat as errors
```

```python
def parse(self, response):
    if response.status == 404:
        self.logger.warning(f"Page not found: {response.url}")
        return
    # Normal processing...
```

---

## Performance

### Concurrent Requests

```python
# settings.py
CONCURRENT_REQUESTS = 16  # Total concurrent requests
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # Per domain
CONCURRENT_REQUESTS_PER_IP = 0  # Per IP (0 = disabled)
```

### DNS Caching

```python
# settings.py
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
```

### HTTP Caching (Development)

```python
# settings.py
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_EXPIRATION_SECS = 86400  # 1 day
```

### Memory Usage

```python
# settings.py
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024
```

### Autothrottle

```python
# settings.py
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
```

---

## Distributed Crawling

### Multiple Scrapyd Instances

Partition URLs across multiple Scrapyd instances. Pass spider arguments to coordinate which subset each instance processes.

### Scrapy-Redis

For distributed crawling with shared queue:

```bash
pip install scrapy-redis
```

```python
# settings.py
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
REDIS_URL = "redis://localhost:6379"
```

### Frontera

For large-scale distributed crawling with politeness controls.

---

## Project Structure

```
myproject/
├── scrapy.cfg
├── myproject/
│   ├── __init__.py
│   ├── items.py          # Item definitions
│   ├── loaders.py        # ItemLoader classes
│   ├── middlewares.py    # Custom middlewares
│   ├── pipelines.py      # Item pipelines
│   ├── settings.py       # Project settings
│   └── spiders/
│       ├── __init__.py
│       └── myspider.py
└── tests/
    └── test_spider.py
```

---

## Sources

- [Scrapy Official Documentation](https://docs.scrapy.org/en/latest/)
- [Scrapy Common Practices](https://docs.scrapy.org/en/latest/topics/practices.html)
- [Scrapy Item Pipeline](https://docs.scrapy.org/en/latest/topics/item-pipeline.html)
- [Scrapy Item Loaders](https://docs.scrapy.org/en/latest/topics/loaders.html)
- [Scrapy Spiders](https://docs.scrapy.org/en/latest/topics/spiders.html)
- [ScrapeOps Scrapy Guides](https://scrapeops.io/python-scrapy-playbook/)
- [Apify - Data in Scrapy](https://blog.apify.com/data-in-scrapy-databases-pipelines/)
- [Zyte - DeltaFetch](https://www.zyte.com/blog/scrapy-tips-from-the-pros-july-2016/)
- [Scrapfly - Scrapy Guide 2025](https://scrapfly.io/blog/posts/web-scraping-with-scrapy)
