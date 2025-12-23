import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "dental_scraper"
SPIDER_MODULES = ["dental_scraper.spiders"]
NEWSPIDER_MODULE = "dental_scraper.spiders"

ROBOTSTXT_OBEY = os.getenv("RESPECT_ROBOTS_TXT", "true").lower() == "true"

CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "4"))
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", "3"))
RANDOMIZE_DOWNLOAD_DELAY = os.getenv("RANDOMIZE_DOWNLOAD_DELAY", "true").lower() == "true"

CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2

CLOSESPIDER_TIMEOUT = int(os.getenv("CLOSESPIDER_TIMEOUT", "0"))
CLOSESPIDER_PAGECOUNT = int(os.getenv("CLOSESPIDER_PAGECOUNT", "0"))

COOKIES_ENABLED = True

DOWNLOADER_MIDDLEWARES = {
    "dental_scraper.middlewares.RandomUserAgentMiddleware": 400,
    "dental_scraper.middlewares.PlaywrightCleanupMiddleware": 1000,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
}

ITEM_PIPELINES = {
    "dental_scraper.pipelines.cleaner.CleanerPipeline": 100,
    "dental_scraper.pipelines.normalizer.NormalizerPipeline": 200,
    "dental_scraper.pipelines.exporter.JsonExporterPipeline": 300,
}

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
    "args": [
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-software-rasterizer",
    ],
}

PLAYWRIGHT_MAX_CONTEXTS = 3
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 4
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

PLAYWRIGHT_CONTEXTS = {
    "default": {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
        "java_script_enabled": True,
    }
}

PLAYWRIGHT_ABORT_REQUEST = lambda req: req.resource_type in [
    "image", "media", "font", "stylesheet"
]

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

FEED_EXPORT_ENCODING = "utf-8"
