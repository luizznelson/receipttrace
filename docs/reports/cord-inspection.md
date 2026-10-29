# Inspeção inicial do CORD v2

## Resultado desta etapa

Foram selecionados 20 recibos reais com origem e integridade verificáveis. A inspeção mostrou quais campos tinham anotação suficiente para uma primeira comparação e identificou limitações dos layouts. Nenhum extrator foi avaliado nesta etapa.

Registro histórico: descreve o que foi verificado nesta etapa. O [relatório comparativo atual](gemini-development-20.md) apresenta os resultados posteriores de OCR e Gemini.

Data: 28/10/2026. Esta é uma inspeção de dados, não avaliação de um extrator.

## Proveniência

Fonte: NAVER CLOVA, CORD v2, https://huggingface.co/datasets/naver-clova-ix/cord-v2
Autores e documentação: https://github.com/clovaai/cord
Licença: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
Revisão: `7f0115a4b758a71d6473b8d085751692da2fef98`.

O primeiro arquivo de treino contém 200 linhas e ocupa 490.224.630 bytes. O download foi comparado ao SHA-256 publicado pelo repositório de origem. Foram selecionadas 20 linhas sem reposição, com semente 42. Os IDs e hashes estão no [manifesto publicado](cord-inspection.manifest.json).

## Contagens automatizadas

| Campo | Presença | Denominador |
|---|---:|---:|
| Descrição do item | 27 | 27 itens de primeiro nível |
| Quantidade do item | 25 | 27 itens de primeiro nível |
| Preço unitário | 15 | 27 itens de primeiro nível |
| Preço do item | 27 | 27 itens de primeiro nível |
| Total do recibo | 19 | 20 documentos |
| Subtotal | 14 | 20 documentos |

As contagens indicam presença da chave nas anotações, não correção do valor ou legibilidade. Itens subordinados em `sub` não estão incluídos na contagem de primeiro nível. Não houve imagens idênticas byte a byte dentro da amostra; duplicatas entre divisões não foram investigadas.

## Revisão visual exploratória

Foram abertos os documentos de linhas 6, 7 e 22. Observações limitadas a esses três: há inclinação/perspectiva, dobras e diferenças de iluminação; trechos já vêm ocultados na fonte. Há vírgulas e pontos em valores e marcadores de quantidade como `1x`. A revisão visual completa dos 20 documentos ainda está pendente. Nenhum arquivo de imagem foi alterado ou publicado neste relatório.

## Decisões para a próxima etapa

- Descrição e preço por item são candidatos ao núcleo do esquema.
- Quantidade, preço unitário e total são opcionais; ausência não deve gerar preenchimento presumido.
- Guardar o texto original antes de normalizar números; não interpretar separadores usando automaticamente o padrão brasileiro.
- Normalizar `menu` objeto/lista sem descartar os itens subordinados na implementação do domínio.
- Verificar relações aritméticas somente quando os componentes necessários existirem. Divergência exige análise: não prova erro comercial.

## Reprodução

Na raiz: `uv sync --locked`, `uv run receipttrace prepare-cord`, `uv run receipttrace verify-sample`.
Se a saída já existe, use outro diretório: `uv run receipttrace prepare-cord --output data/processed/cord-repeat`.
Compare IDs e hashes com o manifesto publicado; datas de execução naturalmente variam. Os dados permanecem fora do Git.

## Limites

Amostra de um único arquivo de treino, sem representatividade estatística assegurada. Nenhum modelo foi executado e não há métricas de extração, custo ou latência. Nenhum documento de validação ou teste foi baixado. O uso de um benchmark público não elimina a possibilidade de exposição prévia dos modelos a seus dados. Resultados futuros deverão ser apresentados como benchmark público, não como validação comercial independente.
