# Dental Speed - Estrutura e Seletores

## Estrutura de URLs

### Categorias
- Padrao: `https://www.dentalspeed.com/{categoria}.html`
- Subcategorias: `https://www.dentalspeed.com/{categoria}/{subcategoria}.html`
- Exemplos:
  - `/descartaveis.html`
  - `/descartaveis/luvas.html`
  - `/dentistica-e-estetica/resina-composta.html`

### Produtos
- Padrao: `https://www.dentalspeed.com/{slug-produto}-{id}.html`
- O ID numerico esta sempre no final antes de `.html`
- Exemplos:
  - `/luva-para-procedimento-de-latex-com-po-descarpack-16939.html`
  - `/resina-forma-ultradent-12189.html`

## Pagina de Listagem de Produtos

### Estrutura do Card de Produto
```
- Link para produto
- Imagem do produto
- Badge (OFERTA, Novidade, DESCONTO PROGRESSIVO)
- Nome do produto
- Marca
- Descricao curta
- Avaliacao (estrelas + quantidade)
- Preco original (riscado)
- Preco promocional
- Percentual de desconto
- Botao "Adicionar" ou "Ver Opcoes"
```

### Seletores para Listagem
| Campo | Seletor |
|-------|---------|
| Container produtos | `.products-grid .item`, `.products.list .product` |
| Link produto | `a::attr(href)` |
| Nome produto | `strong a::text` |
| Marca | Texto apos o nome |
| Preco | Elemento com `R$XX,XX` |
| Badge | Elementos com texto OFERTA, Novidade |

## Pagina de Detalhe do Produto (PDP)

### Estrutura Principal
```
- Breadcrumbs: Home > Categoria > Subcategoria > Produto
- Galeria de imagens (carousel)
- Titulo (h1)
- Subtitulo (h2) - descricao da embalagem
- Codigo de Referencia
- Avaliacao (estrelas + contagem)
- Regras promocionais
- Seletor de variantes (tamanho, cor)
- Preco
- Quantidade
- Botao Adicionar ao Carrinho
- Calculadora de frete (CEP)
- Beneficios (Mais Speed, Frete Gratis, Troca Gratis)
- Abas (Formas de pagamento, Detalhes, Mais Informacoes, Aplicacao)
- Secao de perguntas e respostas
- Avaliacoes de clientes
- Produtos relacionados (Compre junto)
- Produtos similares
```

### Seletores para PDP

| Campo | Seletor | Notas |
|-------|---------|-------|
| Nome | `h1::text` | Titulo principal |
| Descricao | `h2::text` | Subtitulo com info da embalagem |
| SKU | XPath: `//*[contains(text(), 'Cod. de Referência:')]` | Extrair numero |
| SKU (fallback) | URL: `-(\d+)\.html$` | Regex do ID no final da URL |
| Marca | Tabela "Mais Informacoes" | `//tr[contains(., 'Marca')]/td[last()]/text()` |
| Marca (fallback) | `a[href*='/marcas/']::text` | Link para pagina da marca |
| Preco promocional | Elemento com `R$XX,XX` apos "A partir de" | |
| Preco original | Elemento riscado antes do preco atual | |
| Imagem | `img[src*='cdn.dentalspeed.com']::attr(src)` | CDN de imagens |
| Categoria | Breadcrumbs | `ol li a::text` - excluir Home e produto |
| Variantes (select) | `select option::text` | Para cores |
| Variantes (listbox) | `div[@role='listbox'] div[@role='option']` | Para tamanhos |
| Em estoque | Presenca de `button:contains('Adicionar ao Carrinho')` | |

### Extracao de Quantidade da Descricao

Padroes no subtitulo (h2):
- "Embalagem com 100 unidades"
- "Embalagem com 1 seringa de 4g"
- "Embalagem com 10 caixas de 100 unidades cada"
- "Embalagem com 1 par"

Regex:
```python
patterns = [
    r"com\s+(\d+)\s+unidades",
    r"(\d+)\s+unidades",
    r"c/\s*(\d+)",
    r"embalagem\s+com\s+(\d+)",
]
```

### Extracao de Unidade da Descricao

| Palavra-chave | Unidade |
|---------------|---------|
| caixa, cx | caixa |
| pacote, pct | pacote |
| kit | kit |
| seringa | seringa |
| frasco | frasco |
| tubo | tubo |
| par | par |
| unidade, un | unidade |

## Calculadora de Frete (Funcionalidade Futura)

### Localizacao
- Secao "Calcular frete e prazo" na PDP
- Input para CEP (8 digitos)
- Botao "Calcular"

### Dados Retornados
- Prazo de entrega (dias)
- Valor do frete
- Metodo de envio

### Implementacao Futura
Para coletar dados de frete por CEP:
1. Navegar para PDP
2. Selecionar variante (se necessario)
3. Inserir CEP no input
4. Clicar em Calcular
5. Aguardar resposta AJAX
6. Extrair dados de frete

### CEPs de Teste Sugeridos
- 01310-100 (Sao Paulo - SP)
- 22041-080 (Rio de Janeiro - RJ)
- 88010-000 (Florianopolis - SC)
- 30130-000 (Belo Horizonte - MG)
- 40020-000 (Salvador - BA)

## Abas de Informacao

### Detalhes
- Descricao completa do produto
- Caracteristicas (lista)
- Especificacoes tecnicas (tabela)
- Links para PDFs (Instrucoes de Uso, Cartela de Cores)

### Mais Informacoes
- Tabela com atributos estruturados
- Sempre inclui "Marca"

### Aplicacao
- Indicacoes de uso clinico

### Informacoes Adicionais
- Dados complementares (nem todos produtos tem)

## Avaliacoes

### Estrutura
- Media geral (ex: 4,5)
- Distribuicao por estrelas
- Percentual de recomendacao
- Lista de avaliacoes individuais:
  - Estrelas
  - Titulo
  - Comentario
  - Autor
  - Data
  - Badge "Compra verificada"
  - Indicador "Recomendaria"
  - Votos uteis

## Notas Importantes

1. O site usa JavaScript para carregar algumas informacoes - necessario Playwright
2. Precos podem variar por regra promocional (compre X pague Y)
3. Algumas variantes tem precos diferentes
4. Imagens estao no CDN: cdn.dentalspeed.com
5. O site tem politica anti-bot - usar delays e rotacao de user-agent
