# Dental Scraper

Scraper para coleta de dados de produtos de fornecedores odontologicos brasileiros.

## Requisitos

- Python 3.11+
- Playwright

## Instalacao

```bash
cd dental-scraper

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

pip install -e ".[dev]"

playwright install chromium
```

## Configuracao

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

## Uso

### Executar spider individual

```bash
scrapy crawl dental_speed
```

### Executar com output especifico

```bash
scrapy crawl dental_speed -o output/dental_speed.json
```

### Listar spiders disponiveis

```bash
scrapy list
```

## Testes

```bash
pytest
pytest tests/test_normalizer/ -v
pytest --cov=dental_scraper
```

## Estrutura

```
dental_scraper/
├── spiders/          # Um spider por fornecedor
├── pipelines/        # Cleaner, Normalizer, Exporter
├── normalization/    # Regras de normalizacao (marcas, unidades, categorias)
├── matching/         # Matching de produtos (fase 2)
└── utils/            # Utilitarios
```

## Fornecedores

| Fornecedor | Spider | Status |
|------------|--------|--------|
| Dental Speed | `dental_speed` | Em desenvolvimento |
| Dental Cremer | `dental_cremer` | Planejado |
| Surya Dental | `surya_dental` | Planejado |
| Dental Partner | `dental_partner` | Planejado |
| Dental Med Sul | `dental_medsul` | Planejado |

## Pipeline de Dados

1. **CleanerPipeline** - Limpeza de HTML, encoding
2. **NormalizerPipeline** - Normalizacao de marcas, unidades, categorias
3. **JsonExporterPipeline** - Exporta para JSON/CSV
