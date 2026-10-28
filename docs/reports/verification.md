# Verificação local — 28/10/2026

Ambiente: Windows, Python 3.14.3, uv 0.12.5. Dependências: uv.lock.

- `uv sync --locked`: concluído.
- `uv run ruff format --check .`: aprovado.
- `uv run ruff check .`: aprovado.
- `uv run mypy`: aprovado, três módulos de origem verificados.
- `uv run pytest`: 11 testes aprovados, sem rede nos testes.
- `uv run receipttrace prepare-cord`: aquisição e inspeção de 20 documentos reais concluídas.
- `uv run receipttrace verify-sample`: 20 documentos verificados.
- Repetição com outro diretório: mesmos IDs, índices, hashes de imagens/anotações e contagens.
- Links Markdown locais dos READMEs e documentos: verificados.

A CI foi configurada, mas não foi executada remotamente nesta sessão. Não foram criados commits nem realizados push/deploy. Extração, API, interface e benchmark de modelos ainda não estão implementados.
