import json
from datetime import datetime
from urllib.parse import urlencode

from scrapy import Request, Spider

from dental_scraper.items import RawProductItem


class DentalSpeedSpider(Spider):
    name = "dental_speed"
    allowed_domains = ["api.linximpulse.com", "dentalspeed.com"]

    API_BASE = "https://api.linximpulse.com/engage/search/v3/navigates"
    API_KEY = "dentalspeed-api"
    RESULTS_PER_PAGE = 100

    CATEGORIES = [
        "descartaveis",
        "biosseguranca",
        "moldagem-e-modelo",
        "anestesicos-e-agulha-gengival",
        "equipamentos",
        "pecas-de-mao",
        "instrumentais",
        "higiene-oral",
        "consultorio-odontologico",
        "prevencao-e-profilaxia",
        "papelaria-personalizada",
        "brocas",
        "equipamentos-laboratoriais",
        "fotografia",
        "limpeza-e-saneantes",
        "organizadores",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4,
        "DEFAULT_REQUEST_HEADERS": {
            "Origin": "https://www.dentalspeed.com",
            "Referer": "https://www.dentalspeed.com/",
            "Accept": "application/json",
        },
    }

    def start_requests(self):
        for category in self.CATEGORIES:
            url = self._build_url(category, page=1)
            yield Request(
                url=url,
                callback=self.parse_category,
                meta={"category": category, "page": 1},
                errback=self.handle_error,
            )

    def _build_url(self, category: str, page: int) -> str:
        params = {
            "page": page,
            "multicategory": category,
            "sortby": "relevance",
            "resultsperpage": self.RESULTS_PER_PAGE,
            "apiKey": self.API_KEY,
            "source": "desktop",
        }
        return f"{self.API_BASE}?{urlencode(params)}"

    def parse_category(self, response):
        category = response.meta["category"]
        page = response.meta["page"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON for {category} page {page}: {e}")
            return

        products = data.get("products", [])
        total = data.get("size", 0)

        self.logger.info(f"Category {category} page {page}: {len(products)} products (total: {total})")

        for product in products:
            item = self._parse_product(product, category)
            yield Request(
                url=item["external_url"],
                callback=self.parse_html_for_enrichment,
                meta={"item": item},
                errback=self.handle_enrichment_error,
                priority=-1,
            )

        if products:
            total_pages = (total + self.RESULTS_PER_PAGE - 1) // self.RESULTS_PER_PAGE
            if page < total_pages:
                next_url = self._build_url(category, page + 1)
                yield Request(
                    url=next_url,
                    callback=self.parse_category,
                    meta={"category": category, "page": page + 1},
                    errback=self.handle_error,
                )

    def _parse_product(self, product: dict, category: str) -> RawProductItem:
        item = RawProductItem()
        item["supplier"] = "Dental Speed"
        item["external_id"] = product.get("id", "")
        item["raw_name"] = product.get("name", "")
        item["external_url"] = f"https://www.dentalspeed.com{product.get('url', '')}"
        item["currency"] = "BRL"
        item["scraped_at"] = datetime.now().isoformat()

        price = product.get("price")
        if price:
            item["price"] = float(price)

        old_price = product.get("oldPrice")
        if old_price and old_price != price:
            item["original_price"] = float(old_price)

        skus = product.get("skus", [])
        if skus:
            sku_data = skus[0]
            properties = sku_data.get("properties", {})
            details = properties.get("details", {})

            pix_price = self._get_detail(details, "price_with_discount_pix")
            if pix_price:
                try:
                    item["pix_price"] = float(pix_price)
                except (ValueError, TypeError):
                    pass

            brand = self._get_detail(details, "brand")
            if brand:
                item["raw_brand"] = brand

            manufacturer_code = self._get_detail(details, "cod_fabricante")
            if manufacturer_code:
                item["manufacturer_code"] = manufacturer_code

            discount = self._get_detail(details, "percentDiscount")
            if discount:
                try:
                    item["discount_percent"] = int(discount)
                except (ValueError, TypeError):
                    pass

        categories = product.get("categories", [])
        if categories:
            cat_names = [c.get("name") for c in categories if c.get("name")]
            for cat_name in cat_names:
                item["raw_category"] = cat_name

        status = product.get("status")
        item["in_stock"] = status == "AVAILABLE" if status else True

        images = product.get("images", {})
        if isinstance(images, dict):
            image_url = images.get("default") or images.get("small") or images.get("medium")
            if image_url:
                item["image_url"] = image_url

        return item

    def _get_detail(self, details: dict, key: str):
        value = details.get(key)
        if isinstance(value, list) and value:
            return value[0]
        return value

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")

    def parse_html_for_enrichment(self, response):
        item = response.meta["item"]

        anvisa = self._extract_anvisa(response)
        if anvisa:
            item["anvisa_registration"] = anvisa

        ean = self._extract_ean(response)
        if ean:
            item["ean"] = ean

        yield item

    def handle_enrichment_error(self, failure):
        item = failure.request.meta.get("item")
        if item:
            self.logger.warning(f"HTML enrichment failed for {item.get('external_id')}: {failure.value}")
            yield item

    def _extract_anvisa(self, response) -> str | None:
        for item in response.css("li.line-attr-product"):
            label = item.css("span.type::text").get()
            if label and "anvisa" in label.lower():
                value = item.css("span.value::text").get()
                if value:
                    return value.strip()
        return None

    def _extract_ean(self, response) -> str | None:
        for item in response.css("li.line-attr-product"):
            label = item.css("span.type::text").get()
            if label and ("ean" in label.lower() or "código de barras" in label.lower()):
                value = item.css("span.value::text").get()
                if value:
                    return value.strip()
        return None
