from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Product:
    supplier: str
    external_id: str
    external_url: str
    name: str
    normalized_name: str
    brand: str
    normalized_brand: str
    category: str
    quantity: int
    unit: str
    price: Optional[Decimal]
    pix_price: Optional[Decimal]
    ean: Optional[str]
    manufacturer_code: Optional[str]
    anvisa_registration: Optional[str]
    in_stock: bool

    @property
    def uid(self) -> str:
        return f"{self.supplier}:{self.external_id}"

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        return cls(
            supplier=data.get("supplier", ""),
            external_id=data.get("external_id", ""),
            external_url=data.get("external_url", ""),
            name=data.get("name", ""),
            normalized_name=data.get("normalized_name", ""),
            brand=data.get("brand", ""),
            normalized_brand=data.get("normalized_brand", ""),
            category=data.get("category", ""),
            quantity=data.get("quantity", 1),
            unit=data.get("unit", "unidade"),
            price=Decimal(str(data["price"])) if data.get("price") else None,
            pix_price=Decimal(str(data["pix_price"])) if data.get("pix_price") else None,
            ean=data.get("ean"),
            manufacturer_code=data.get("manufacturer_code"),
            anvisa_registration=data.get("anvisa_registration"),
            in_stock=data.get("in_stock", False),
        )


@dataclass
class Match:
    confidence: float
    method: str


@dataclass
class ProductMatch:
    product_a: Product
    product_b: Product
    confidence: float
    method: str
    status: str = "confirmed"
    matched_at: datetime = field(default_factory=datetime.now)

    @property
    def price_diff_absolute(self) -> Optional[Decimal]:
        if self.product_a.price and self.product_b.price:
            return self.product_b.price - self.product_a.price
        return None

    @property
    def price_diff_percent(self) -> Optional[float]:
        if self.product_a.price and self.product_b.price and self.product_a.price > 0:
            diff = float(self.product_b.price - self.product_a.price)
            return round((diff / float(self.product_a.price)) * 100, 2)
        return None

    @property
    def cheaper_supplier(self) -> Optional[str]:
        if self.product_a.price and self.product_b.price:
            if self.product_a.price < self.product_b.price:
                return self.product_a.supplier
            elif self.product_b.price < self.product_a.price:
                return self.product_b.supplier
        return None

    def to_dict(self) -> dict:
        return {
            "product_a": {
                "supplier": self.product_a.supplier,
                "external_id": self.product_a.external_id,
                "name": self.product_a.name,
                "price": float(self.product_a.price) if self.product_a.price else None,
                "pix_price": float(self.product_a.pix_price) if self.product_a.pix_price else None,
            },
            "product_b": {
                "supplier": self.product_b.supplier,
                "external_id": self.product_b.external_id,
                "name": self.product_b.name,
                "price": float(self.product_b.price) if self.product_b.price else None,
                "pix_price": float(self.product_b.pix_price) if self.product_b.pix_price else None,
            },
            "confidence": self.confidence,
            "method": self.method,
            "status": self.status,
            "price_diff_percent": self.price_diff_percent,
            "cheaper_at": self.cheaper_supplier,
            "matched_at": self.matched_at.isoformat(),
        }


@dataclass
class MatchResult:
    matches: list[ProductMatch]
    unmatched_a: list[Product]
    unmatched_b: list[Product]

    @property
    def stats(self) -> dict:
        methods = {}
        for m in self.matches:
            methods[m.method] = methods.get(m.method, 0) + 1

        return {
            "total_matches": len(self.matches),
            "by_method": methods,
            "unmatched_a": len(self.unmatched_a),
            "unmatched_b": len(self.unmatched_b),
        }

    def to_dict(self) -> dict:
        return {
            "matches": [m.to_dict() for m in self.matches],
            "stats": self.stats,
        }
