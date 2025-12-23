import re
from datetime import datetime
from urllib.parse import urlparse

from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from dental_scraper.items import RawProductItem
from dental_scraper.loaders import DentalSpeedLoader


class DentalSpeedSpider(CrawlSpider):
    name = "dental_speed"
    allowed_domains = ["dentalspeed.com", "www.dentalspeed.com"]
    start_urls = [
        "https://www.dentalspeed.com/descartaveis.html",
        "https://www.dentalspeed.com/biosseguranca.html",
        "https://www.dentalspeed.com/moldagem-e-modelo.html",
        "https://www.dentalspeed.com/anestesicos-e-agulha-gengival.html",
        "https://www.dentalspeed.com/equipamentos.html",
        "https://www.dentalspeed.com/pecas-de-mao.html",
        "https://www.dentalspeed.com/instrumentais.html",
        "https://www.dentalspeed.com/higiene-oral.html",
        "https://www.dentalspeed.com/consultorio-odontologico.html",
        "https://www.dentalspeed.com/moda.html",
        "https://www.dentalspeed.com/prevencao-e-profilaxia.html",
        "https://www.dentalspeed.com/papelaria-personalizada.html",
        "https://www.dentalspeed.com/brocas.html",
        "https://www.dentalspeed.com/equipamentos-laboratoriais.html",
        "https://www.dentalspeed.com/fotografia.html",
        "https://www.dentalspeed.com/limpeza-e-saneantes.html",
        "https://www.dentalspeed.com/organizadores.html",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    EXCLUDED_PAGES = {
        "descartaveis.html", "biosseguranca.html", "moldagem-e-modelo.html",
        "equipamentos.html", "instrumentais.html", "higiene-oral.html",
        "moda.html", "brocas.html", "ortodontia.html", "endodontia.html",
        "cirurgia.html", "protese.html", "periodontia.html",
        "anestesicos-e-agulha-gengival.html", "pecas-de-mao.html",
        "consultorio-odontologico.html", "prevencao-e-profilaxia.html",
        "papelaria-personalizada.html", "equipamentos-laboratoriais.html",
        "fotografia.html", "limpeza-e-saneantes.html", "organizadores.html",
    }

    EXCLUDED_KEYWORDS = [
        "politica", "fale-com", "sobre", "programa", "cupom",
        "super-loja", "marcas", "laboratorio", "universitarios",
        "ofertas-materiais", "checkout", "cart", "login", "register",
    ]

    rules = (
        Rule(
            LinkExtractor(allow=r"\.html$", deny=r"\.html\?"),
            process_links="filter_product_links",
            callback="parse_product",
            follow=False,
            process_request="set_playwright_meta",
            errback="handle_error",
        ),
        Rule(
            LinkExtractor(allow=r"\.html\?p=\d+"),
            process_request="set_playwright_meta",
            follow=True,
        ),
    )

    async def start(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                meta={"playwright": True},
                errback=self.handle_error,
            )

    def set_playwright_meta(self, request: Request, response: Response) -> Request:
        request.meta["playwright"] = True
        return request

    def filter_product_links(self, links: list) -> list:
        filtered = []
        for link in links:
            if self._is_product_url(link.url):
                filtered.append(link)
        self.logger.debug(f"Filtered {len(filtered)} product links from {len(links)} total")
        return filtered

    def _is_product_url(self, url: str) -> bool:
        if not url or not url.endswith(".html"):
            return False

        parsed = urlparse(url.lower().strip())
        path = parsed.path.lstrip("/")

        if "/" in path:
            return False

        if path in self.EXCLUDED_PAGES:
            return False

        for keyword in self.EXCLUDED_KEYWORDS:
            if keyword in path:
                return False

        return True

    def parse_product(self, response: Response):
        loader = DentalSpeedLoader(response=response)

        name = response.css("h1::text").get()
        if not name:
            name = response.css(".page-title span::text").get()

        if not name:
            self.logger.warning(f"No product name found: {response.url}")
            return

        has_sku = response.css("#yv-productId::attr(value)").get()
        has_ref = response.xpath("//*[contains(text(), 'Cod. de Referência:')]").get()
        if not has_sku and not has_ref:
            self.logger.debug(f"Skipping non-product page: {response.url}")
            return

        loader.add_value("supplier", "Dental Speed")
        loader.add_value("external_url", response.url)
        loader.add_value("currency", "BRL")
        loader.add_value("scraped_at", datetime.now().isoformat())

        loader.add_css("raw_name", "h1::text")
        loader.add_css("raw_name", ".page-title span::text")

        subtitle = response.css("h2::text").get()
        if subtitle:
            loader.add_value("raw_description", subtitle)
            loader.add_value("raw_unit", subtitle)
            loader.add_value("raw_quantity", subtitle)
        else:
            loader.add_css("raw_description", '[itemprop="description"]::text')
            loader.add_value("raw_unit", "unidade")
            loader.add_value("raw_quantity", 1)

        self._load_price(loader, response)
        self._load_sku(loader, response)
        self._load_brand(loader, response)
        self._load_category(loader, response)
        self._load_availability(loader, response)
        self._load_image(loader, response)
        self._load_variants(loader, response)
        self._load_specifications(loader, response)
        self._load_rating(loader, response)
        self._load_details(loader, response)

        yield loader.load_item()

    def _load_price(self, loader: DentalSpeedLoader, response: Response) -> None:
        data_price = response.css("[data-price-amount]::attr(data-price-amount)").get()
        if data_price:
            try:
                price_value = float(data_price)
                if price_value > 0:
                    loader.add_value("price", price_value)
                    self._load_original_price(loader, response)
                    return
            except ValueError:
                pass

        price_selectors = [
            ".price-wrapper .price::text",
            ".price-box .price::text",
            ".normal-price .price::text",
            "div.price::text",
            "span.price::text",
            "strong.price::text",
            ".price::text",
            '[data-price-type="finalPrice"] .price::text',
            ".price-final_price .price::text",
            ".special-price .price::text",
            ".product-info-price .price::text",
        ]
        for selector in price_selectors:
            price_text = response.css(selector).get()
            if price_text and "R$" in price_text:
                loader.add_css("price", selector)
                self._load_original_price(loader, response)
                return

    def _load_original_price(self, loader: DentalSpeedLoader, response: Response) -> None:
        old_data_price = response.css('[data-price-type="oldPrice"]::attr(data-price-amount)').get()
        if old_data_price:
            try:
                old_price_value = float(old_data_price)
                if old_price_value > 0:
                    loader.add_value("original_price", old_price_value)
                    return
            except ValueError:
                pass

        old_price_selectors = [
            ".old-price .price::text",
            ".price-old .price::text",
            '[data-price-type="oldPrice"] .price::text',
        ]
        for selector in old_price_selectors:
            old_price_text = response.css(selector).get()
            if old_price_text and "R$" in old_price_text:
                loader.add_css("original_price", selector)
                return

    def _load_sku(self, loader: DentalSpeedLoader, response: Response) -> None:
        ref_text = response.xpath(
            "//*[contains(text(), 'Cod. de Referência:')]/following-sibling::*[1]/text()"
        ).get()

        if ref_text:
            loader.add_value("external_id", ref_text.strip())
            return

        full_text = response.xpath(
            "//*[contains(text(), 'Cod. de Referência:')]//text()"
        ).getall()
        for text in full_text:
            match = re.search(r"(\d+)", text)
            if match:
                loader.add_value("external_id", match.group(1))
                return

        match = re.search(r"-(\d+)\.html$", response.url)
        if match:
            loader.add_value("external_id", match.group(1))
            return

        slug = response.url.split("/")[-1].replace(".html", "")
        loader.add_value("external_id", slug)

    def _load_brand(self, loader: DentalSpeedLoader, response: Response) -> None:
        specs_list = response.css("tabpanel[aria-label*='Especificações'] li, [role='tabpanel'] li")
        for item in specs_list:
            label = item.css("div:first-child::text, span:first-child::text").get()
            if label and "marca" in label.lower().strip():
                value = item.css("div:last-child::text, span:last-child::text").get()
                if value:
                    loader.add_value("raw_brand", value.strip())
                    return

        brand_xpath = response.xpath(
            "//li[contains(., 'Marca')]/div[last()]/text() | "
            "//li[contains(., 'Marca')]/span[last()]/text()"
        ).get()
        if brand_xpath:
            loader.add_value("raw_brand", brand_xpath.strip())
            return

        brand_link = response.css("a[href*='/marcas/']::text").get()
        if brand_link:
            loader.add_value("raw_brand", brand_link)

    def _load_category(self, loader: DentalSpeedLoader, response: Response) -> None:
        breadcrumbs = response.css(
            "nav.breadcrumbs li a::text, ul.breadcrumb li a::text, ol li a::text"
        ).getall()
        if breadcrumbs:
            for crumb in breadcrumbs:
                loader.add_value("raw_category", crumb)

    def _load_availability(self, loader: DentalSpeedLoader, response: Response) -> None:
        out_of_stock_selectors = [
            ".stock.unavailable",
            ".out-of-stock",
            '[data-availability="unavailable"]',
        ]

        for selector in out_of_stock_selectors:
            if response.css(selector).get():
                loader.add_value("in_stock", False)
                return

        availability = response.css('[itemprop="availability"]::attr(href)').get()
        if availability and "InStock" in availability:
            loader.add_value("in_stock", True)
            return

        loader.add_value("in_stock", True)

    def _load_image(self, loader: DentalSpeedLoader, response: Response) -> None:
        hidden_input = response.css("#yv-productImage::attr(value)").get()
        if hidden_input and 'cdn.dentalspeed.com' in hidden_input:
            loader.add_value("image_url", hidden_input)
            return

        fotorama_href = response.css(".fotorama__stage__frame::attr(href)").get()
        if fotorama_href and 'cdn.dentalspeed.com' in fotorama_href:
            loader.add_value("image_url", fotorama_href)
            return

        all_images = []
        all_images += response.css("img.fotorama__img::attr(src)").getall()
        all_images += response.css(".fotorama__stage img::attr(src)").getall()
        all_images += response.css("[data-gallery-role] img::attr(src)").getall()
        all_images += response.css(".gallery-placeholder img::attr(src)").getall()
        all_images += response.css("img::attr(src)").getall()

        for img in all_images:
            if img and 'cdn.dentalspeed.com' in img and '/produtos/' in img:
                loader.add_value("image_url", img)
                return

        for img in all_images:
            if img and 'cdn.dentalspeed.com' in img and '/catalog/' in img:
                loader.add_value("image_url", img)
                return


    def _load_variants(self, loader: DentalSpeedLoader, response: Response) -> None:
        options = response.css("select option::text").getall()
        for opt in options:
            opt = opt.strip()
            if opt and opt.lower() not in ["escolha uma opção...", "selecione", ""]:
                loader.add_value("variants", opt)

        if not loader.get_collected_values("variants"):
            listbox_options = response.xpath(
                "//div[@role='listbox']//div[@role='option']/text() | "
                "//ul[@role='listbox']//li/text()"
            ).getall()
            for opt in listbox_options:
                loader.add_value("variants", opt)

    def _load_specifications(self, loader: DentalSpeedLoader, response: Response) -> None:
        specs = {}
        spec_items = response.xpath(
            "//li[contains(@class, '') and .//div[contains(text(), 'Marca') or "
            "contains(text(), 'Código') or contains(text(), 'Área') or "
            "contains(text(), 'Apresentação') or contains(text(), 'Cor') or "
            "contains(text(), 'Especialidade') or contains(text(), 'Tipo') or "
            "contains(text(), 'Procedimento')]]"
        )

        for item in response.css("[role='tabpanel'] li"):
            divs = item.css("div::text").getall()
            if len(divs) >= 2:
                key = divs[0].strip()
                value = divs[1].strip()
                if key and value:
                    specs[key] = value
                    if key.lower() == "código do fabricante":
                        loader.add_value("manufacturer_code", value)

        if specs:
            loader.add_value("specifications", specs)

    def _load_rating(self, loader: DentalSpeedLoader, response: Response) -> None:
        rating_text = response.xpath(
            "//div[contains(@class, 'rating') or contains(@class, 'review')]"
            "//div[contains(text(), ',') or contains(text(), '.')][string-length(text()) < 4]/text()"
        ).get()

        if not rating_text:
            rating_text = response.css("[class*='rating'] [class*='value']::text").get()

        if rating_text:
            try:
                rating = float(rating_text.strip().replace(",", "."))
                if 0 <= rating <= 5:
                    loader.add_value("rating", rating)
            except ValueError:
                pass

        review_count = response.xpath(
            "//strong[contains(text(), '(')]/descendant-or-self::*/text()"
        ).re_first(r"\((\d+)\)")

        if review_count:
            loader.add_value("review_count", int(review_count))

    def _load_details(self, loader: DentalSpeedLoader, response: Response) -> None:
        details_panel = response.xpath(
            "//div[@role='tabpanel'][.//div[contains(text(), 'Detalhes')]] | "
            "//div[contains(@class, 'tab') and contains(@aria-label, 'Detalhes')]"
        )

        details_items = response.css(
            "[role='tabpanel'] li::text, "
            "[role='tabpanel'] li p::text, "
            "[role='tabpanel'] li strong::text"
        ).getall()

        if not details_items:
            details_items = response.xpath(
                "//div[contains(@class, 'tab-content')]//li//text() | "
                "//div[contains(@class, 'product-details')]//li//text()"
            ).getall()

        details = []
        for item in details_items:
            text = item.strip()
            if text and len(text) > 3:
                details.append(text)

        if details:
            loader.add_value("details", details)

    def handle_error(self, failure) -> None:
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
