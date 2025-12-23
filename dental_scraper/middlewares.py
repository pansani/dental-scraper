import logging

from fake_useragent import UserAgent
from scrapy import signals
from scrapy.http import Response


logger = logging.getLogger(__name__)


class RandomUserAgentMiddleware:
    def __init__(self):
        self.ua = UserAgent()

    def process_request(self, request, spider):
        request.headers["User-Agent"] = self.ua.random


class PlaywrightCleanupMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    async def process_response(self, request, response, spider):
        page = request.meta.get("playwright_page")
        if page and not page.is_closed():
            try:
                await page.close()
                logger.debug(f"Closed Playwright page for {request.url}")
            except Exception as e:
                logger.warning(f"Failed to close Playwright page: {e}")
        return response

    async def process_exception(self, request, exception, spider):
        page = request.meta.get("playwright_page")
        if page and not page.is_closed():
            try:
                await page.close()
                logger.debug(f"Closed Playwright page after exception for {request.url}")
            except Exception as e:
                logger.warning(f"Failed to close Playwright page on exception: {e}")
        return None

    def spider_closed(self, spider):
        logger.info("Spider closed - Playwright cleanup complete")
