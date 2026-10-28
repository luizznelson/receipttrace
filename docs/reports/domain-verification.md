# Verificação do domínio — 28/10/2026

Ambiente: Windows, Python 3.14.3, dependências fixadas no uv.lock.

- `uv sync --locked`: ambiente sincronizado com Pydantic.
- Ruff: formatação e análise aprovadas.
- `uv run mypy`: aprovado, cinco módulos de origem.
- `uv run pytest`: 56 testes aprovados, sem rede.
- `uv run receipttrace validate-receipt examples/synthetic-receipt.json --policy idr-grouped`: código 0; três verificações aritméticas aprovadas.
- Exemplo de saída: [synthetic-validation.json](synthetic-validation.json).
- Contrato de entrada: [JSON Schema](../contracts/raw-receipt.schema.json).

Os testes cobrem políticas numéricas, valores ausentes e inválidos, descontos, tolerância, precisão decimal, preservação de subitens, contratos estritos, integridade dos dados e execução do comando. Os casos novos são sintéticos e explicitamente identificados. Não são métricas de extração do CORD.

Ainda pendentes: extrator OCR, adaptador de extração com IA, avaliação dos modelos, API, interface e deploy. A CI não foi executada remotamente nesta sessão. Nenhum commit foi criado.
