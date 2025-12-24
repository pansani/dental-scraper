def normalize_brand(brand: str | None) -> str:
    if not brand:
        return ""
    return brand.strip()


def extract_brand_from_name(product_name: str) -> str | None:
    if not product_name:
        return None

    if " - " in product_name:
        parts = product_name.rsplit(" - ", 1)
        if len(parts) == 2:
            brand = parts[1].strip()
            if brand and len(brand) >= 2:
                return brand

    return None
