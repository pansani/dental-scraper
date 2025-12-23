import json
import re
from datetime import datetime
from urllib.parse import urlparse

from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from dental_scraper.items import RawProductItem
from dental_scraper.loaders import DentalCremerLoader


class DentalCremerSpider(CrawlSpider):
    name = "dental_cremer"
    allowed_domains = ["dentalcremer.com.br", "www.dentalcremer.com.br", "cdn.dentalcremer.com.br"]

    PRICE_API_URL = "https://www.dentalcremer.com.br/rest/V2/hsb_catalog/price"
    PRICE_API_TOKEN = "zziij1y5yvprsfjyyp8i6jhatx7c85fo"

    start_urls = [
        "https://www.dentalcremer.com.br/dentistica-e-estetica.html",
        "https://www.dentalcremer.com.br/cirurgia-e-periodontia.html",
        "https://www.dentalcremer.com.br/endodontia.html",
        "https://www.dentalcremer.com.br/ortodontia.html",
        "https://www.dentalcremer.com.br/implantodontia.html",
        "https://www.dentalcremer.com.br/protese-clinica.html",
        "https://www.dentalcremer.com.br/protese-laboratorial.html",
        "https://www.dentalcremer.com.br/harmonizacao-orofacial.html",
        "https://www.dentalcremer.com.br/radiologia.html",
        "https://www.dentalcremer.com.br/anestesicos-e-agulha-gengival.html",
        "https://www.dentalcremer.com.br/biosseguranca.html",
        "https://www.dentalcremer.com.br/descartaveis.html",
        "https://www.dentalcremer.com.br/moldagem-e-modelo.html",
        "https://www.dentalcremer.com.br/equipamentos.html",
        "https://www.dentalcremer.com.br/instrumentais.html",
        "https://www.dentalcremer.com.br/higiene-oral.html",
        "https://www.dentalcremer.com.br/prevencao-e-profilaxia.html",
        "https://www.dentalcremer.com.br/pecas-de-mao.html",
        "https://www.dentalcremer.com.br/brocas.html",
        "https://www.dentalcremer.com.br/cimentos.html",
        "https://www.dentalcremer.com.br/livraria.html",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 0.5,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
    }

    EXCLUDED_PAGES = {
        "dentistica-e-estetica.html", "cirurgia-e-periodontia.html",
        "endodontia.html", "ortodontia.html", "implantodontia.html",
        "protese-clinica.html", "protese-laboratorial.html",
        "harmonizacao-orofacial.html", "radiologia.html",
        "anestesicos-e-agulha-gengival.html", "biosseguranca.html",
        "descartaveis.html", "moldagem-e-modelo.html", "equipamentos.html",
        "instrumentais.html", "higiene-oral.html", "prevencao-e-profilaxia.html",
        "pecas-de-mao.html", "brocas.html", "cimentos.html", "livraria.html",
        "moda.html", "vestuario.html", "para-o-consultorio.html",
    }

    EXCLUDED_KEYWORDS = [
        "politica", "fale-com", "sobre", "programa", "cupom",
        "super-loja", "marcas", "laboratorio", "estudantes",
        "ofertas", "checkout", "cart", "login", "register",
        "lovers", "ciosp", "empresa", "henry-schein",
    ]

    rules = (
        Rule(
            LinkExtractor(allow=r"\.html$", deny=r"\.html\?"),
            process_links="filter_product_links",
            callback="parse_product",
            follow=False,
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
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context": "default",
                },
                errback=self.handle_error,
            )

    def set_playwright_meta(self, request: Request, response: Response) -> Request:
        request.meta["playwright"] = True
        request.meta["playwright_include_page"] = True
        request.meta["playwright_context"] = "default"
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

        if re.search(r"-dc\d+\.html$", path, re.IGNORECASE):
            return True

        return False

    def parse_product(self, response: Response):
        loader = DentalCremerLoader(response=response)

        product_data = self._extract_product_json(response)

        name = response.css("h1::text").get()
        if not name:
            name = response.css(".page-title span::text").get()

        if not name and not product_data:
            self.logger.warning(f"No product name found: {response.url}")
            return

        has_sku = response.css("#yv-productId::attr(value)").get()
        has_ref = response.xpath("//*[contains(text(), 'Cod. de Referência:')]").get()
        if not has_sku and not has_ref and not product_data:
            self.logger.debug(f"Skipping non-product page: {response.url}")
            return

        loader.add_value("supplier", "Dental Cremer")
        loader.add_value("external_url", response.url)
        loader.add_value("currency", "BRL")
        loader.add_value("scraped_at", datetime.now().isoformat())

        if product_data:
            if product_data.get("name"):
                loader.add_value("raw_name", product_data["name"])
            if product_data.get("price"):
                loader.add_value("price", float(product_data["price"]))
            if product_data.get("id"):
                loader.add_value("external_id", product_data["id"])
            if product_data.get("brand"):
                loader.add_value("raw_brand", product_data["brand"])
            if product_data.get("category"):
                cat = product_data["category"].split(" - ")[0]
                loader.add_value("raw_category", cat)

        if not loader.get_collected_values("raw_name"):
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

        if not loader.get_collected_values("price"):
            self._load_price(loader, response)
        if not loader.get_collected_values("external_id"):
            self._load_sku(loader, response)
        if not loader.get_collected_values("raw_brand"):
            self._load_brand(loader, response)
        if not loader.get_collected_values("raw_category"):
            self._load_category(loader, response)

        self._load_availability(loader, response)
        self._load_image(loader, response)
        self._load_variants(loader, response)
        self._load_specifications(loader, response)
        self._load_rating(loader, response)
        self._load_details(loader, response)
        self._load_restricted_sale(loader, response)
        self._load_pdf_urls(loader, response)
        self._load_full_description(loader, response)
        self._load_max_qty(loader, response)

        item = loader.load_item()
        sku = item.get("external_id")

        if sku:
            yield Request(
                url=f"{self.PRICE_API_URL}?sku={sku}",
                callback=self.parse_price_api,
                meta={
                    "item": item,
                    "playwright": False,
                    "dont_obey_robotstxt": True,
                },
                headers={
                    "Authorization": f"Bearer {self.PRICE_API_TOKEN}",
                    "Referer": response.url,
                    "Accept": "application/json",
                    "Origin": "https://www.dentalcremer.com.br",
                },
                errback=self.handle_price_error,
                dont_filter=True,
            )
        else:
            yield item

    def parse_price_api(self, response: Response):
        item = response.meta["item"]
        sku = item.get("external_id")

        try:
            data = json.loads(response.text)
            if isinstance(data, list) and len(data) > 0:
                product_price = data[0].get(sku, {}).get("main", {})
                price = product_price.get("special_price") or product_price.get("price")
                if price:
                    item["price"] = float(price)
                    self.logger.debug(f"Got price {price} from API for {sku}")

                original = product_price.get("price")
                if original and product_price.get("special_price"):
                    item["original_price"] = float(original)

                pix_price = product_price.get("price_with_discount")
                if pix_price:
                    item["pix_price"] = float(pix_price)

                installments = product_price.get("installments")
                if installments:
                    item["installments"] = installments

                discount_percent = product_price.get("percent_discount")
                if discount_percent:
                    item["discount_percent"] = int(discount_percent)

                can_scheduled = product_price.get("can_scheduledbuy")
                if can_scheduled is not None:
                    item["can_scheduled_buy"] = can_scheduled

                scheduled_price = product_price.get("scheduledbuy_price")
                if scheduled_price:
                    item["scheduled_buy_price"] = float(scheduled_price)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            self.logger.warning(f"Failed to parse price API response for {sku}: {e}")

        if item.get("restricted_sale") and sku:
            yield Request(
                url=f"https://www.dentalcremer.com.br/rest/V2/hsb_label/messages/{sku}?device=browser",
                callback=self.parse_messages_api,
                meta={"item": item, "playwright": False, "dont_obey_robotstxt": True},
                headers={
                    "Authorization": f"Bearer {self.PRICE_API_TOKEN}",
                    "Accept": "application/json",
                },
                errback=self.handle_messages_error,
                dont_filter=True,
            )
        else:
            yield item

    def handle_price_error(self, failure):
        item = failure.request.meta.get("item")
        self.logger.warning(f"Price API error: {failure.value}")
        if item:
            self.logger.warning(f"Price API failed for {item.get('external_id')}, yielding without price")
            yield item

    def parse_messages_api(self, response: Response):
        item = response.meta["item"]
        try:
            data = json.loads(response.text)
            if isinstance(data, list) and len(data) > 0:
                messages = [msg.get("info") or msg.get("text") for msg in data if msg.get("type") == "alert"]
                if messages:
                    item["restricted_sale_message"] = messages[0]
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.warning(f"Failed to parse messages API: {e}")
        yield item

    def handle_messages_error(self, failure):
        item = failure.request.meta.get("item")
        self.logger.warning(f"Messages API error: {failure.value}")
        if item:
            yield item

    def _extract_product_json(self, response: Response) -> dict | None:
        pattern = r'"product"\s*:\s*(\{[^}]+\})'
        match = response.css("script::text").re_first(pattern)
        if match:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                pass
        return None

    def _load_price(self, loader: DentalCremerLoader, response: Response) -> None:
        json_ld_scripts = response.css('script[type="application/ld+json"]::text').getall()
        for script in json_ld_scripts:
            try:
                data = json.loads(script)
                if isinstance(data, dict):
                    price = self._extract_price_from_json_ld(data)
                    if price:
                        loader.add_value("price", price)
                        return
                elif isinstance(data, list):
                    for item in data:
                        price = self._extract_price_from_json_ld(item)
                        if price:
                            loader.add_value("price", price)
                            return
            except (json.JSONDecodeError, TypeError):
                continue

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

    def _extract_price_from_json_ld(self, data: dict) -> float | None:
        if not isinstance(data, dict):
            return None

        if data.get("@type") == "Product":
            offers = data.get("offers", {})
            if isinstance(offers, dict):
                price = offers.get("price")
                if price:
                    try:
                        return float(price)
                    except (ValueError, TypeError):
                        pass

        if "price" in data:
            try:
                return float(data["price"])
            except (ValueError, TypeError):
                pass

        return None

    def _load_original_price(self, loader: DentalCremerLoader, response: Response) -> None:
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

    def _load_sku(self, loader: DentalCremerLoader, response: Response) -> None:
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
            match = re.search(r"(DC\d+)", text, re.IGNORECASE)
            if match:
                loader.add_value("external_id", match.group(1).upper())
                return

        match = re.search(r"-(dc\d+)\.html$", response.url, re.IGNORECASE)
        if match:
            loader.add_value("external_id", match.group(1).upper())
            return

        slug = response.url.split("/")[-1].replace(".html", "")
        loader.add_value("external_id", slug)

    def _load_brand(self, loader: DentalCremerLoader, response: Response) -> None:
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

    def _load_category(self, loader: DentalCremerLoader, response: Response) -> None:
        breadcrumbs = response.css(
            "nav.breadcrumbs li a::text, ul.breadcrumb li a::text, ol li a::text"
        ).getall()
        if breadcrumbs:
            for crumb in breadcrumbs:
                loader.add_value("raw_category", crumb)

    def _load_availability(self, loader: DentalCremerLoader, response: Response) -> None:
        notify_me_selectors = [
            'a:contains("Avise-me quando chegar")',
            'button:contains("Avise-me quando chegar")',
            '[href*="productalert/add/stock"]',
        ]

        for selector in notify_me_selectors:
            if response.css(selector).get():
                loader.add_value("in_stock", False)
                return

        notify_xpath = response.xpath(
            "//*[contains(text(), 'Avise-me quando chegar')]"
        ).get()
        if notify_xpath:
            loader.add_value("in_stock", False)
            return

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
        if availability:
            if "InStock" in availability:
                loader.add_value("in_stock", True)
                return
            if "OutOfStock" in availability:
                loader.add_value("in_stock", False)
                return

        add_to_cart = response.css(
            'button:contains("Adicionar ao Carrinho"), '
            'button[data-action="add-to-cart"], '
            '#product-addtocart-button'
        ).get()
        if add_to_cart:
            loader.add_value("in_stock", True)
            return

        loader.add_value("in_stock", False)

    def _load_image(self, loader: DentalCremerLoader, response: Response) -> None:
        hidden_input = response.css("#yv-productImage::attr(value)").get()
        if hidden_input and 'cdn.dentalcremer.com.br' in hidden_input:
            loader.add_value("image_url", hidden_input)
            return

        fotorama_href = response.css(".fotorama__stage__frame::attr(href)").get()
        if fotorama_href and 'cdn.dentalcremer.com.br' in fotorama_href:
            loader.add_value("image_url", fotorama_href)
            return

        all_images = []
        all_images += response.css("img.fotorama__img::attr(src)").getall()
        all_images += response.css(".fotorama__stage img::attr(src)").getall()
        all_images += response.css("[data-gallery-role] img::attr(src)").getall()
        all_images += response.css(".gallery-placeholder img::attr(src)").getall()
        all_images += response.css("img::attr(src)").getall()

        for img in all_images:
            if img and 'cdn.dentalcremer.com.br' in img and '/produtos/' in img:
                loader.add_value("image_url", img)
                return

        for img in all_images:
            if img and 'cdn.dentalcremer.com.br' in img and '/catalog/' in img:
                loader.add_value("image_url", img)
                return


    def _load_variants(self, loader: DentalCremerLoader, response: Response) -> None:
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

    def _load_specifications(self, loader: DentalCremerLoader, response: Response) -> None:
        specs = {}

        field_mappings = {
            "ean (código de barras)": "ean",
            "ean": "ean",
            "registro anvisa": "anvisa_registration",
            "área profissional": "professional_area",
            "especialidade": "specialty",
            "procedimento": "procedure",
            "código do fabricante": "manufacturer_code",
        }

        for item in response.css("li.line-attr-product"):
            key = item.css("span.type::text").get()
            value = item.css("span.value::text").get()
            if key and value:
                key = key.strip()
                value = value.strip()
                specs[key] = value
                key_lower = key.lower()
                if key_lower in field_mappings:
                    loader.add_value(field_mappings[key_lower], value)

        if specs:
            loader.add_value("specifications", specs)

    def _load_rating(self, loader: DentalCremerLoader, response: Response) -> None:
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

    def _load_details(self, loader: DentalCremerLoader, response: Response) -> None:
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

    def _load_restricted_sale(self, loader: DentalCremerLoader, response: Response) -> None:
        restricted_patterns = [
            "venda restrita",
            "venda sob prescrição",
            "uso exclusivamente profissional",
            "produto controlado",
        ]
        page_text = response.xpath("//body//text()").getall()
        page_text = " ".join(page_text).lower()

        for pattern in restricted_patterns:
            if pattern in page_text:
                loader.add_value("restricted_sale", True)
                return
        loader.add_value("restricted_sale", False)

    def _load_pdf_urls(self, loader: DentalCremerLoader, response: Response) -> None:
        pdf_links = response.css("a[href$='.pdf']::attr(href)").getall()
        pdf_links += response.xpath("//a[contains(@href, '.pdf')]/@href").getall()

        product_pdfs = [
            pdf for pdf in set(pdf_links)
            if "cdn.dentalcremer.com.br" in pdf
        ]
        if product_pdfs:
            loader.add_value("pdf_urls", product_pdfs)

    def _load_full_description(self, loader: DentalCremerLoader, response: Response) -> None:
        description_parts = []

        details_panel = response.xpath(
            "//div[@role='tabpanel']//div[contains(@class, 'prose')] | "
            "//div[@role='tabpanel']//div[contains(@class, 'content')] | "
            "//div[contains(@class, 'product-info')]//div[contains(@class, 'description')]"
        )

        if details_panel:
            texts = details_panel.xpath(".//text()").getall()
            description_parts.extend([t.strip() for t in texts if t.strip()])

        if not description_parts:
            all_tabs = response.css("[role='tabpanel']")
            for tab in all_tabs:
                paragraphs = tab.css("p::text, div.prose::text, li::text").getall()
                description_parts.extend([p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10])

        if description_parts:
            full_text = "\n".join(description_parts)
            loader.add_value("full_description", full_text)

    def _load_max_qty(self, loader: DentalCremerLoader, response: Response) -> None:
        qty_limit = response.css("script::text").re_first(r'"qtyLimit"\s*:\s*(\d+)')
        if qty_limit:
            loader.add_value("max_qty_per_order", int(qty_limit))

    def handle_error(self, failure) -> None:
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
