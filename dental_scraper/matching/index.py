from collections import defaultdict
from typing import Optional

from .models import Product


class MatchIndex:
    def __init__(self):
        self.by_ean: dict[str, list[Product]] = defaultdict(list)
        self.by_manufacturer_code: dict[str, list[Product]] = defaultdict(list)
        self.by_anvisa: dict[str, list[Product]] = defaultdict(list)
        self.by_brand_category: dict[str, list[Product]] = defaultdict(list)
        self.all_products: list[Product] = []

    def add(self, product: Product) -> None:
        self.all_products.append(product)

        if product.ean:
            self.by_ean[product.ean].append(product)

        if product.manufacturer_code and product.normalized_brand:
            key = f"{product.normalized_brand}:{product.manufacturer_code}"
            self.by_manufacturer_code[key].append(product)

        if product.anvisa_registration:
            self.by_anvisa[product.anvisa_registration].append(product)

        if product.normalized_brand and product.category:
            key = f"{product.normalized_brand}:{product.category}"
            self.by_brand_category[key].append(product)

    def add_many(self, products: list[Product]) -> None:
        for product in products:
            self.add(product)

    def find_by_ean(self, ean: str) -> list[Product]:
        return self.by_ean.get(ean, [])

    def find_by_manufacturer_code(self, brand: str, code: str) -> list[Product]:
        key = f"{brand}:{code}"
        return self.by_manufacturer_code.get(key, [])

    def find_by_anvisa(self, anvisa: str) -> list[Product]:
        return self.by_anvisa.get(anvisa, [])

    def find_by_brand_category(self, brand: str, category: str) -> list[Product]:
        key = f"{brand}:{category}"
        return self.by_brand_category.get(key, [])

    def find_candidates(self, product: Product) -> list[Product]:
        candidates = set()

        if product.ean:
            for p in self.find_by_ean(product.ean):
                if p.uid != product.uid:
                    candidates.add(p.uid)

        if product.manufacturer_code and product.normalized_brand:
            for p in self.find_by_manufacturer_code(
                product.normalized_brand, product.manufacturer_code
            ):
                if p.uid != product.uid:
                    candidates.add(p.uid)

        if product.anvisa_registration:
            for p in self.find_by_anvisa(product.anvisa_registration):
                if p.uid != product.uid:
                    candidates.add(p.uid)

        if product.normalized_brand and product.category:
            for p in self.find_by_brand_category(
                product.normalized_brand, product.category
            ):
                if p.uid != product.uid:
                    candidates.add(p.uid)

        uid_to_product = {p.uid: p for p in self.all_products}
        return [uid_to_product[uid] for uid in candidates if uid in uid_to_product]

    def __len__(self) -> int:
        return len(self.all_products)

    def stats(self) -> dict:
        return {
            "total_products": len(self.all_products),
            "with_ean": len(self.by_ean),
            "with_manufacturer_code": len(self.by_manufacturer_code),
            "with_anvisa": len(self.by_anvisa),
            "by_brand_category": len(self.by_brand_category),
        }
