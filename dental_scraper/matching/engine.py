from typing import Optional

from .index import MatchIndex
from .models import MatchResult, Product, ProductMatch
from .similarity import compute_similarity


class MatchingEngine:
    def __init__(self, fuzzy_threshold: float = 0.70):
        self.fuzzy_threshold = fuzzy_threshold

    def match(
        self,
        products_a: list[Product],
        products_b: list[Product],
    ) -> MatchResult:
        index_b = MatchIndex()
        index_b.add_many(products_b)

        matches: list[ProductMatch] = []
        matched_a_uids: set[str] = set()
        matched_b_uids: set[str] = set()

        for product_a in products_a:
            best_match: Optional[ProductMatch] = None
            best_confidence = 0.0

            candidates = index_b.find_candidates(product_a)

            if not candidates:
                candidates = [
                    p for p in products_b
                    if p.normalized_brand
                    and product_a.normalized_brand
                    and p.normalized_brand.lower() == product_a.normalized_brand.lower()
                ]

            for product_b in candidates:
                if product_b.uid in matched_b_uids:
                    continue

                result = compute_similarity(product_a, product_b)
                if result and result.confidence > best_confidence:
                    best_confidence = result.confidence
                    best_match = ProductMatch(
                        product_a=product_a,
                        product_b=product_b,
                        confidence=result.confidence,
                        method=result.method,
                        status="confirmed" if result.confidence >= 0.85 else "pending",
                    )

            if best_match and best_match.confidence >= self.fuzzy_threshold:
                matches.append(best_match)
                matched_a_uids.add(product_a.uid)
                matched_b_uids.add(best_match.product_b.uid)

        unmatched_a = [p for p in products_a if p.uid not in matched_a_uids]
        unmatched_b = [p for p in products_b if p.uid not in matched_b_uids]

        matches.sort(key=lambda m: m.confidence, reverse=True)

        return MatchResult(
            matches=matches,
            unmatched_a=unmatched_a,
            unmatched_b=unmatched_b,
        )

    def match_all_pairs(self, products: list[Product]) -> MatchResult:
        by_supplier: dict[str, list[Product]] = {}
        for p in products:
            if p.supplier not in by_supplier:
                by_supplier[p.supplier] = []
            by_supplier[p.supplier].append(p)

        suppliers = list(by_supplier.keys())
        if len(suppliers) < 2:
            return MatchResult(matches=[], unmatched_a=products, unmatched_b=[])

        products_a = by_supplier[suppliers[0]]
        products_b = by_supplier[suppliers[1]]

        return self.match(products_a, products_b)
