import re
from typing import Any

from scrapy.loader import ItemLoader
from itemloaders.processors import Compose, Identity, MapCompose, TakeFirst

from dental_scraper.items import RawProductItem


def clean_text(value) -> str:
    if not value or not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def parse_brazilian_price(value) -> float | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = str(value).strip()
        cleaned = cleaned.replace("R$", "").replace("$", "")
        cleaned = cleaned.replace(" ", "")
        cleaned = cleaned.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def extract_quantity(subtitle: str) -> int:
    if not subtitle:
        return 1

    patterns = [
        r"com\s+(\d+)\s+unidades",
        r"(\d+)\s+unidades",
        r"c/\s*(\d+)",
        r"embalagem\s+com\s+(\d+)",
        r"(\d+)\s*un\b",
        r"(\d+)\s*pcs",
        r"(\d+)\s*peças",
    ]

    subtitle_lower = subtitle.lower()
    for pattern in patterns:
        match = re.search(pattern, subtitle_lower)
        if match:
            qty = int(match.group(1))
            if qty <= 10000:
                return qty

    return 1


def extract_unit(subtitle: str) -> str:
    if not subtitle:
        return "unidade"

    subtitle_lower = subtitle.lower()

    unit_patterns = [
        (["caixa", "cx"], "caixa"),
        (["pacote", "pct"], "pacote"),
        (["kit"], "kit"),
        (["seringa"], "seringa"),
        (["frasco"], "frasco"),
        (["tubo"], "tubo"),
        (["par"], "par"),
        (["unidade", "un"], "unidade"),
    ]

    for keywords, unit in unit_patterns:
        for keyword in keywords:
            if keyword in subtitle_lower:
                return unit

    return "unidade"


def filter_empty(values: list[Any]) -> list[Any]:
    return [v for v in values if v]


def join_categories(values: list[str]) -> str:
    filtered = [v.strip() for v in values if v and v.strip().lower() != "home"]
    if len(filtered) > 1:
        return " > ".join(filtered[:-1])
    elif filtered:
        return filtered[0]
    return ""


class DentalSpeedLoader(ItemLoader):
    default_item_class = RawProductItem
    default_input_processor = MapCompose(clean_text)
    default_output_processor = TakeFirst()

    raw_name_in = MapCompose(clean_text)
    raw_name_out = TakeFirst()

    raw_description_in = MapCompose(clean_text)
    raw_description_out = TakeFirst()

    raw_brand_in = MapCompose(clean_text)
    raw_brand_out = TakeFirst()

    price_in = MapCompose(parse_brazilian_price)
    price_out = TakeFirst()

    original_price_in = MapCompose(parse_brazilian_price)
    original_price_out = TakeFirst()

    raw_category_in = MapCompose(clean_text)
    raw_category_out = Compose(filter_empty, join_categories)

    raw_unit_in = MapCompose(extract_unit)
    raw_unit_out = TakeFirst()

    raw_quantity_in = MapCompose(extract_quantity)
    raw_quantity_out = TakeFirst()

    variants_in = MapCompose(clean_text)
    variants_out = Compose(filter_empty, list)

    image_url_in = Identity()
    image_url_out = TakeFirst()

    external_url_in = Identity()
    external_url_out = TakeFirst()

    external_id_in = MapCompose(clean_text)
    external_id_out = TakeFirst()

    supplier_in = Identity()
    supplier_out = TakeFirst()

    currency_in = Identity()
    currency_out = TakeFirst()

    in_stock_in = Identity()
    in_stock_out = TakeFirst()

    scraped_at_in = Identity()
    scraped_at_out = TakeFirst()

    manufacturer_code_in = MapCompose(clean_text)
    manufacturer_code_out = TakeFirst()

    specifications_in = Identity()
    specifications_out = TakeFirst()

    rating_in = Identity()
    rating_out = TakeFirst()

    review_count_in = Identity()
    review_count_out = TakeFirst()

    details_in = Identity()
    details_out = TakeFirst()
