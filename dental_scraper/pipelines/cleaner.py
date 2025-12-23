import re

from w3lib.html import remove_tags

from dental_scraper.items import RawProductItem


class CleanerPipeline:
    def process_item(self, item: RawProductItem, spider) -> RawProductItem:
        text_fields = [
            "raw_name",
            "raw_description",
            "raw_category",
            "raw_brand",
            "raw_unit",
        ]

        for field in text_fields:
            if field in item and item[field]:
                item[field] = self._clean_text(item[field])

        if "price" in item and item["price"]:
            item["price"] = self._clean_price(item["price"])

        if "original_price" in item and item["original_price"]:
            item["original_price"] = self._clean_price(item["original_price"])

        if "external_url" in item and item["external_url"]:
            item["external_url"] = item["external_url"].strip()

        return item

    def _clean_text(self, text: str | None) -> str:
        if not text:
            return ""
        if isinstance(text, list):
            text = " ".join(str(t) for t in text)
        text = str(text)
        text = remove_tags(text)
        text = text.encode("utf-8", errors="ignore").decode("utf-8")
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def _clean_price(self, price) -> float | None:
        if price is None:
            return None
        if isinstance(price, (int, float)):
            return float(price)
        if isinstance(price, str):
            try:
                cleaned = price.strip()
                cleaned = re.sub(r"[R$\s]", "", cleaned)
                cleaned = cleaned.replace(".", "").replace(",", ".")
                return float(cleaned)
            except (ValueError, AttributeError):
                return None
        return None
