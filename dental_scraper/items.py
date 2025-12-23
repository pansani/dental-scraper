from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

import scrapy


class RawProductItem(scrapy.Item):
    supplier = scrapy.Field()
    external_id = scrapy.Field()
    external_url = scrapy.Field()
    raw_name = scrapy.Field()
    raw_description = scrapy.Field()
    raw_category = scrapy.Field()
    raw_brand = scrapy.Field()
    raw_unit = scrapy.Field()
    raw_quantity = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    currency = scrapy.Field()
    in_stock = scrapy.Field()
    image_url = scrapy.Field()
    scraped_at = scrapy.Field()
    variants = scrapy.Field()
    manufacturer_code = scrapy.Field()
    specifications = scrapy.Field()
    rating = scrapy.Field()
    review_count = scrapy.Field()
    details = scrapy.Field()
    ean = scrapy.Field()
    anvisa_registration = scrapy.Field()
    restricted_sale = scrapy.Field()
    professional_area = scrapy.Field()
    specialty = scrapy.Field()
    procedure = scrapy.Field()
    pdf_urls = scrapy.Field()
    full_description = scrapy.Field()
    pix_price = scrapy.Field()
    installments = scrapy.Field()
    discount_percent = scrapy.Field()
    max_qty_per_order = scrapy.Field()
    can_scheduled_buy = scrapy.Field()
    scheduled_buy_price = scrapy.Field()
    restricted_sale_message = scrapy.Field()


class NormalizedProductItem(scrapy.Item):
    supplier = scrapy.Field()
    external_id = scrapy.Field()
    external_url = scrapy.Field()
    name = scrapy.Field()
    normalized_name = scrapy.Field()
    description = scrapy.Field()
    raw_category_path = scrapy.Field()
    category = scrapy.Field()
    category_confidence = scrapy.Field()
    brand = scrapy.Field()
    normalized_brand = scrapy.Field()
    unit = scrapy.Field()
    quantity = scrapy.Field()
    price = scrapy.Field()
    original_price = scrapy.Field()
    currency = scrapy.Field()
    in_stock = scrapy.Field()
    image_url = scrapy.Field()
    scraped_at = scrapy.Field()
    ean = scrapy.Field()
    anvisa_registration = scrapy.Field()
    restricted_sale = scrapy.Field()
    professional_area = scrapy.Field()
    specialty = scrapy.Field()
    procedure = scrapy.Field()
    pdf_urls = scrapy.Field()
    manufacturer_code = scrapy.Field()
    specifications = scrapy.Field()
    pix_price = scrapy.Field()
    installments = scrapy.Field()
    discount_percent = scrapy.Field()
    max_qty_per_order = scrapy.Field()
    can_scheduled_buy = scrapy.Field()
    scheduled_buy_price = scrapy.Field()
    restricted_sale_message = scrapy.Field()


@dataclass
class Product:
    supplier: str
    external_id: str
    external_url: str
    name: str
    normalized_name: str = ""
    description: str = ""
    category: str = ""
    brand: str = ""
    normalized_brand: str = ""
    unit: str = "unidade"
    quantity: int = 1
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    currency: str = "BRL"
    in_stock: bool = False
    image_url: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "supplier": self.supplier,
            "external_id": self.external_id,
            "external_url": self.external_url,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "normalized_brand": self.normalized_brand,
            "unit": self.unit,
            "quantity": self.quantity,
            "price": str(self.price) if self.price else None,
            "original_price": str(self.original_price) if self.original_price else None,
            "currency": self.currency,
            "in_stock": self.in_stock,
            "image_url": self.image_url,
            "scraped_at": self.scraped_at.isoformat(),
        }
