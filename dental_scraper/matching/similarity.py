from typing import Optional

from rapidfuzz import fuzz

from .models import Match, Product


def exact_match(product_a: Product, product_b: Product) -> Optional[Match]:
    if product_a.ean and product_b.ean and product_a.ean == product_b.ean:
        return Match(confidence=1.0, method="ean")

    if (
        product_a.manufacturer_code
        and product_b.manufacturer_code
        and product_a.manufacturer_code == product_b.manufacturer_code
        and product_a.normalized_brand
        and product_b.normalized_brand
        and product_a.normalized_brand.lower() == product_b.normalized_brand.lower()
    ):
        return Match(confidence=1.0, method="manufacturer_code")

    if (
        product_a.anvisa_registration
        and product_b.anvisa_registration
        and product_a.anvisa_registration == product_b.anvisa_registration
    ):
        return Match(confidence=0.95, method="anvisa")

    return None


def fuzzy_match(
    product_a: Product,
    product_b: Product,
    threshold: float = 0.70,
    min_name_similarity: float = 0.60,
) -> Optional[Match]:
    weights = {
        "name": 0.40,
        "brand": 0.25,
        "category": 0.15,
        "quantity": 0.10,
        "unit": 0.10,
    }

    score = 0.0

    name_sim = 0.0
    if product_a.normalized_name and product_b.normalized_name:
        name_sim = fuzz.token_sort_ratio(
            product_a.normalized_name,
            product_b.normalized_name,
        ) / 100
        score += name_sim * weights["name"]

    if name_sim < min_name_similarity:
        return None

    if product_a.normalized_brand and product_b.normalized_brand:
        brand_sim = fuzz.ratio(
            product_a.normalized_brand.lower(),
            product_b.normalized_brand.lower(),
        ) / 100
        score += brand_sim * weights["brand"]
    elif not product_a.normalized_brand and not product_b.normalized_brand:
        score += weights["brand"] * 0.5

    if product_a.category and product_b.category:
        if product_a.category == product_b.category:
            score += weights["category"]
        else:
            cat_sim = fuzz.ratio(product_a.category, product_b.category) / 100
            score += cat_sim * weights["category"] * 0.5

    if product_a.quantity == product_b.quantity:
        score += weights["quantity"]
    elif product_a.quantity and product_b.quantity:
        ratio = min(product_a.quantity, product_b.quantity) / max(
            product_a.quantity, product_b.quantity
        )
        score += ratio * weights["quantity"] * 0.5

    if product_a.unit and product_b.unit:
        if product_a.unit.lower() == product_b.unit.lower():
            score += weights["unit"]

    if score >= threshold:
        return Match(confidence=round(score, 3), method="fuzzy")

    return None


def compute_similarity(product_a: Product, product_b: Product) -> Optional[Match]:
    exact = exact_match(product_a, product_b)
    if exact:
        return exact

    return fuzzy_match(product_a, product_b)
