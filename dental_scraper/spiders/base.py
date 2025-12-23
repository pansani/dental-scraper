from abc import abstractmethod
from datetime import datetime
from typing import Any, AsyncGenerator, Generator

import scrapy
from scrapy.http import Response

from dental_scraper.items import RawProductItem


class BaseDentalSpider(scrapy.Spider):
    supplier_name: str = ""
    base_url: str = ""
    use_playwright: bool = False

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.supplier_name:
            raise ValueError("supplier_name must be set")
        if not self.base_url:
            raise ValueError("base_url must be set")

    async def start(self) -> AsyncGenerator[scrapy.Request, None]:
        for url in self.get_category_urls():
            meta = {}
            if self.use_playwright:
                meta["playwright"] = True
                meta["playwright_include_page"] = True
            yield scrapy.Request(
                url=url,
                callback=self.parse_category,
                meta=meta,
            )

    @abstractmethod
    def get_category_urls(self) -> list[str]:
        pass

    @abstractmethod
    def parse_category(self, response: Response) -> Generator[Any, None, None]:
        pass

    @abstractmethod
    def parse_product(self, response: Response) -> Generator[RawProductItem, None, None]:
        pass

    def create_item(
        self,
        external_id: str,
        external_url: str,
        raw_name: str,
        price: float | None = None,
        **kwargs,
    ) -> RawProductItem:
        item = RawProductItem()
        item["supplier"] = self.supplier_name
        item["external_id"] = external_id
        item["external_url"] = external_url
        item["raw_name"] = raw_name
        item["price"] = price
        item["currency"] = kwargs.get("currency", "BRL")
        item["in_stock"] = kwargs.get("in_stock", False)
        item["scraped_at"] = datetime.now().isoformat()

        optional_fields = [
            "raw_description",
            "raw_category",
            "raw_brand",
            "raw_unit",
            "original_price",
            "image_url",
            "variants",
        ]
        for field in optional_fields:
            if field in kwargs:
                item[field] = kwargs[field]

        if "quantity" in kwargs:
            item["raw_quantity"] = kwargs["quantity"]
        elif "raw_quantity" in kwargs:
            item["raw_quantity"] = kwargs["raw_quantity"]

        return item

    def extract_price(self, price_text: str) -> float | None:
        if not price_text:
            return None
        try:
            cleaned = price_text.strip()
            cleaned = cleaned.replace("R$", "").replace("$", "")
            cleaned = cleaned.replace(" ", "")
            cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, AttributeError):
            self.logger.warning(f"Failed to parse price: {price_text}")
            return None

    def extract_sku(self, url: str, response: Response = None) -> str:
        if "/p/" in url:
            parts = url.split("/p/")
            if len(parts) > 1:
                return parts[1].split("/")[0].split("?")[0]
        if response:
            sku = response.css('[data-sku]::attr(data-sku)').get()
            if sku:
                return sku
            sku = response.css('[itemprop="sku"]::attr(content)').get()
            if sku:
                return sku
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:12]
