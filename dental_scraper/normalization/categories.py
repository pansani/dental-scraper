from dental_scraper.normalization.text import normalize_text

CATEGORY_MAPPINGS: dict[str, dict[str, list[str]]] = {
    "Consumíveis": {
        "Anestésicos": [
            "anestesico", "anestesia", "lidocaina", "mepivacaina",
            "articaina", "prilocaina", "anesthetic",
        ],
        "Resinas": [
            "resina", "composto", "composite", "restaurador",
            "z350", "z250", "filtek", "charisma", "empress",
        ],
        "Cimentos": [
            "cimento", "ionomer", "ionomero", "resinoso",
            "provisorio", "definitivo", "cement",
        ],
        "Adesivos": [
            "adesivo", "bond", "bonding", "primer", "single bond",
            "scotchbond", "adhesive",
        ],
        "Descartáveis": [
            "luva", "mascara", "sugador", "gaze", "algodao",
            "babador", "guardanapo", "touca", "propé", "avental",
        ],
        "Endodontia": [
            "lima", "endodontico", "guta", "obturador", "localizador",
            "canal", "hipoclorito", "edta", "file", "rotary",
        ],
        "Profilaxia": [
            "pasta profilatica", "escova robinson", "taca borracha",
            "polimento", "profilaxia", "prophylaxis",
        ],
        "Clareamento": [
            "clareador", "peróxido", "whitening", "branqueamento",
            "clareamento",
        ],
        "Moldagem": [
            "alginato", "silicone", "moldeira", "gesso", "molde",
            "impression", "putty",
        ],
    },
    "Instrumentos": {
        "Manuais": [
            "cureta", "espatula", "sonda", "pinça", "tesoura",
            "porta agulha", "afastador", "espelho",
        ],
        "Rotatórios": [
            "broca", "ponta diamantada", "fresa", "mandril",
            "disco", "tira de lixa", "bur", "drill",
        ],
        "Cirúrgicos": [
            "elevador", "forceps", "alavanca", "sindesmotomo",
            "bisturi", "sutura", "fio cirurgico",
        ],
    },
    "Equipamentos": {
        "Fotopolimerizadores": [
            "fotopolimerizador", "led", "luz", "curing",
            "polimerizar",
        ],
        "Ultrassom": [
            "ultrassom", "ultrasonic", "piezo", "scaler",
        ],
        "Autoclave": [
            "autoclave", "esterilizador", "estufa", "sterilizer",
        ],
        "Raio-X": [
            "raio-x", "radiografia", "sensor", "filme", "revelador",
            "x-ray", "radiograph",
        ],
    },
    "Higiene": {
        "Escovas": [
            "escova dental", "escova interdental", "brush",
        ],
        "Fio Dental": [
            "fio dental", "fita dental", "floss",
        ],
        "Enxaguantes": [
            "enxaguante", "antisseptico", "clorexidina", "mouthwash",
        ],
    },
}

_CATEGORY_KEYWORDS: list[tuple[str, str, str]] = []
for main_cat, subcats in CATEGORY_MAPPINGS.items():
    for subcat, keywords in subcats.items():
        for kw in keywords:
            _CATEGORY_KEYWORDS.append((normalize_text(kw), main_cat, subcat))

_CATEGORY_KEYWORDS.sort(key=lambda x: len(x[0]), reverse=True)


def normalize_category(category: str | None, product_name: str = "") -> tuple[str, str]:
    search_text = normalize_text(f"{category or ''} {product_name}")
    for keyword, main_cat, subcat in _CATEGORY_KEYWORDS:
        if keyword in search_text:
            return main_cat, subcat
    return "Outros", "Geral"


def get_category_path(category: str | None, product_name: str = "") -> str:
    main_cat, subcat = normalize_category(category, product_name)
    return f"{main_cat} > {subcat}"
