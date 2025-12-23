from dental_scraper.items import NormalizedProductItem, RawProductItem
from dental_scraper.normalization import (
    clean_text,
    normalize_brand,
    normalize_category,
    normalize_text,
    normalize_unit,
)
from dental_scraper.normalization.brands import extract_brand_from_name
from dental_scraper.normalization.text import extract_quantity, remove_quantity_from_name
from dental_scraper.normalization.units import extract_unit_from_name


class NormalizerPipeline:
    def process_item(self, item: RawProductItem, spider) -> NormalizedProductItem:
        normalized = NormalizedProductItem()

        normalized["supplier"] = item.get("supplier", "")
        normalized["external_id"] = item.get("external_id", "")
        normalized["external_url"] = item.get("external_url", "")
        normalized["price"] = item.get("price")
        normalized["original_price"] = item.get("original_price")
        normalized["currency"] = item.get("currency", "BRL")
        normalized["in_stock"] = item.get("in_stock", False)
        normalized["image_url"] = item.get("image_url", "")
        normalized["scraped_at"] = item.get("scraped_at", "")

        raw_name = item.get("raw_name", "")
        raw_brand = item.get("raw_brand", "")
        raw_category = item.get("raw_category", "")
        raw_unit = item.get("raw_unit", "")
        raw_quantity = item.get("raw_quantity")

        if raw_brand:
            brand = normalize_brand(raw_brand)
        else:
            brand = extract_brand_from_name(raw_name) or ""

        normalized["brand"] = raw_brand
        normalized["normalized_brand"] = brand

        if raw_unit:
            unit = normalize_unit(raw_unit)
        else:
            unit = extract_unit_from_name(raw_name)
        normalized["unit"] = unit

        if raw_quantity:
            try:
                quantity = int(raw_quantity)
            except (ValueError, TypeError):
                quantity, _ = extract_quantity(raw_name)
        else:
            quantity, _ = extract_quantity(raw_name)
        normalized["quantity"] = quantity

        name = clean_text(raw_name)
        name = remove_quantity_from_name(name, quantity)
        normalized["name"] = name
        normalized["normalized_name"] = normalize_text(name)

        main_cat, sub_cat = normalize_category(raw_category, raw_name)
        normalized["category"] = f"{main_cat} > {sub_cat}"

        description = item.get("raw_description", "")
        normalized["description"] = clean_text(description) if description else ""

        normalized["ean"] = item.get("ean")
        normalized["anvisa_registration"] = item.get("anvisa_registration")
        normalized["restricted_sale"] = item.get("restricted_sale", False)
        normalized["professional_area"] = item.get("professional_area")
        normalized["specialty"] = item.get("specialty")
        normalized["procedure"] = item.get("procedure")
        normalized["pdf_urls"] = item.get("pdf_urls")
        normalized["manufacturer_code"] = item.get("manufacturer_code")
        normalized["specifications"] = item.get("specifications")
        normalized["pix_price"] = item.get("pix_price")
        normalized["installments"] = item.get("installments")
        normalized["discount_percent"] = item.get("discount_percent")
        normalized["max_qty_per_order"] = item.get("max_qty_per_order")
        normalized["can_scheduled_buy"] = item.get("can_scheduled_buy")
        normalized["scheduled_buy_price"] = item.get("scheduled_buy_price")
        normalized["restricted_sale_message"] = item.get("restricted_sale_message")

        return normalized
