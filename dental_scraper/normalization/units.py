from dental_scraper.normalization.text import normalize_text

UNIT_MAPPINGS: dict[str, list[str]] = {
    "unidade": ["un", "und", "unid", "pcs", "pc", "peca", "peça", "unit", "units"],
    "caixa": ["cx", "cxa", "box", "caixas"],
    "pacote": ["pct", "pkt", "pack", "pacotes", "embalagem", "emb"],
    "frasco": ["fr", "frs", "vidro", "frascos"],
    "tubo": ["tb", "bisnaga", "tubos", "bisnagas"],
    "rolo": ["rl", "bobina", "rolos"],
    "kit": ["kits", "conjunto", "set"],
    "seringa": ["ser", "seringas", "syringe"],
    "refil": ["refis", "reposicao", "refill"],
    "cartucho": ["cart", "cartuchos", "cartridge"],
    "blister": ["blisters", "cartela"],
    "envelope": ["envelopes", "sachê", "sache"],
    "galao": ["gal", "galoes"],
    "litro": ["l", "lt", "litros"],
    "mililitro": ["ml", "mililitros"],
    "grama": ["g", "gr", "gramas"],
    "quilograma": ["kg", "quilos", "kilo"],
}

_UNIT_ALIAS_MAP: dict[str, str] = {}
for canonical, aliases in UNIT_MAPPINGS.items():
    _UNIT_ALIAS_MAP[canonical] = canonical
    for alias in aliases:
        _UNIT_ALIAS_MAP[alias.lower()] = canonical


def normalize_unit(unit: str | None) -> str:
    if not unit:
        return "unidade"
    normalized = normalize_text(unit)
    if normalized in _UNIT_ALIAS_MAP:
        return _UNIT_ALIAS_MAP[normalized]
    for alias, canonical in _UNIT_ALIAS_MAP.items():
        if alias in normalized:
            return canonical
    return "unidade"


def extract_unit_from_name(product_name: str) -> str:
    normalized = normalize_text(product_name)
    priority_units = ["caixa", "pacote", "kit", "frasco", "tubo", "seringa", "refil"]
    for unit in priority_units:
        if unit in normalized:
            return unit
        for alias in UNIT_MAPPINGS.get(unit, []):
            if f" {alias} " in f" {normalized} ":
                return unit
    return "unidade"
