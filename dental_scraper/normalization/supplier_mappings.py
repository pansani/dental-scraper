from pathlib import Path
from typing import Optional

import yaml

_MAPPINGS_DIR = Path(__file__).parent.parent / "mappings"
_SUPPLIER_MAPPINGS: dict[str, dict[str, str]] = {}


def _load_mappings() -> None:
    global _SUPPLIER_MAPPINGS
    if _SUPPLIER_MAPPINGS:
        return

    if not _MAPPINGS_DIR.exists():
        return

    for yaml_file in _MAPPINGS_DIR.glob("*.yaml"):
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "supplier" in data and "mappings" in data:
                supplier_key = data["supplier"].lower().replace(" ", "_")
                _SUPPLIER_MAPPINGS[supplier_key] = data["mappings"]


def get_supplier_category(
    supplier: str, raw_category: str
) -> Optional[tuple[str, str]]:
    _load_mappings()

    supplier_key = supplier.lower().replace(" ", "_")
    mappings = _SUPPLIER_MAPPINGS.get(supplier_key, {})

    if raw_category in mappings:
        category_path = mappings[raw_category]
        if " > " in category_path:
            main_cat, sub_cat = category_path.split(" > ", 1)
            return main_cat.strip(), sub_cat.strip()
        return category_path.strip(), "Geral"

    return None


def reload_mappings() -> None:
    global _SUPPLIER_MAPPINGS
    _SUPPLIER_MAPPINGS = {}
    _load_mappings()
