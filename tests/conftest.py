import pytest


@pytest.fixture
def sample_raw_product():
    return {
        "supplier": "Dental Speed",
        "external_id": "12345",
        "external_url": "https://example.com/product/12345",
        "raw_name": "Resina 3M Filtek Z350 XT A2 4g",
        "raw_brand": "3M",
        "raw_category": "Restauração",
        "raw_unit": "un",
        "price": 150.00,
        "in_stock": True,
    }


@pytest.fixture
def sample_normalized_product():
    return {
        "supplier": "Dental Speed",
        "external_id": "12345",
        "external_url": "https://example.com/product/12345",
        "name": "Resina Filtek Z350 XT A2 4g",
        "normalized_name": "resina filtek z350 xt a2 4g",
        "brand": "3M",
        "normalized_brand": "3m",
        "category": "Consumíveis > Resinas",
        "unit": "unidade",
        "quantity": 1,
        "price": 150.00,
        "in_stock": True,
    }
