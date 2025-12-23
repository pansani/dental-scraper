from dental_scraper.normalization.text import normalize_text

BRAND_ALIASES: dict[str, list[str]] = {
    "3m": ["3m oral care", "3m espe", "3m do brasil", "3m unitek", "3m dental"],
    "dentsply": ["dentsply sirona", "dentsply brasil", "dentsply maillefer", "dentsply tulsa"],
    "colgate": ["colgate palmolive", "colgate professional", "colgate total"],
    "coltene": ["coltene whaledent", "coltene vigodent", "vigodent"],
    "ivoclar": ["ivoclar vivadent", "ivoclar"],
    "kerr": ["kerr dental", "kerr corporation", "kerr hawe"],
    "kavo": ["kavo kerr", "kavo do brasil"],
    "maquira": ["maquira dental", "maquira produtos odontologicos"],
    "angelus": ["angelus dental", "angelus industria"],
    "fgm": ["fgm dental", "fgm produtos odontologicos"],
    "ultradent": ["ultradent products", "ultradent do brasil"],
    "gc": ["gc america", "gc dental", "gc corporation"],
    "biodinamica": ["biodinamica quimica", "biodinamica"],
    "kulzer": ["kulzer dental", "heraeus kulzer"],
    "voco": ["voco gmbh", "voco dental"],
    "shofu": ["shofu dental", "shofu inc"],
    "septodont": ["septodont brasil", "septodont"],
    "dfl": ["dfl industria", "dfl dental"],
    "ss white": ["sswhite", "ss white duflex"],
    "densell": ["densell dental"],
    "technew": ["technew comercio"],
    "allprime": ["allprime dental"],
    "nova dfl": ["nova dfl", "novadfl"],
}

_NORMALIZED_BRAND_MAP: dict[str, str] = {}
for canonical, aliases in BRAND_ALIASES.items():
    _NORMALIZED_BRAND_MAP[normalize_text(canonical)] = canonical
    for alias in aliases:
        _NORMALIZED_BRAND_MAP[normalize_text(alias)] = canonical


def normalize_brand(brand: str | None) -> str:
    if not brand:
        return ""
    normalized = normalize_text(brand)
    if normalized in _NORMALIZED_BRAND_MAP:
        return _NORMALIZED_BRAND_MAP[normalized]
    for key, canonical in _NORMALIZED_BRAND_MAP.items():
        if key in normalized or normalized in key:
            return canonical
    return brand.strip()


def extract_brand_from_name(product_name: str) -> str | None:
    normalized = normalize_text(product_name)
    for key, canonical in _NORMALIZED_BRAND_MAP.items():
        if key in normalized:
            return canonical
    return None
