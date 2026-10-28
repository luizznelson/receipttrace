# Ambiente e aquisição dos dados

## Requisitos
Python 3.14 e uv. A versão exata de cada dependência está no uv.lock. Execute na raiz do repositório:

```powershell
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

Os testes são locais, usam fixtures sintéticas explícitas e não baixam o CORD nem fazem chamadas de IA.

## Aquisição e inspeção reais

```powershell
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
```

O primeiro comando baixa aproximadamente 490 MB, verifica o SHA-256 oficial do primeiro arquivo de treino e seleciona 20 linhas com semente 42. Não baixa validação ou teste. A revisão e o hash da fonte estão fixados no código; atualizar a fonte exige revisão explícita.

`data/raw/cord/download.json` registra a aquisição. `data/processed/cord-inspection/manifest.json` registra IDs, hashes, campos e amostragem. `inputs/` contém somente imagens; `reference/` contém anotações para avaliação, que não devem entrar no extrator. A amostra é de apenas um arquivo do treino: não representa toda a base e não mede qualidade de extração.

O diretório de saída deve ser novo. Uma repetição pode usar `--output data/processed/cord-repeat`; o arquivo original já verificado é reutilizado. Datas variam, mas IDs e hashes da amostra são estáveis. Arquivos corrompidos provocam erro explícito. Downloads interrompidos não são publicados como completos; a próxima tentativa recomeça o download.

## Dados e atribuição
Fonte: NAVER CLOVA, CORD v2, https://huggingface.co/datasets/naver-clova-ix/cord-v2
Repositório e autores: https://github.com/clovaai/cord
Licença declarada pelos autores: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
Imagens são preservadas byte a byte. Anotações são serializadas novamente em JSON, sem alteração semântica. Os dados não entram no Git. Relatórios agregados revisados ficam em `docs/reports/`.

O manifesto detecta alterações locais acidentais; ele não é uma assinatura digital. Duplicatas são verificadas apenas dentro da amostra. Duplicação entre divisões, revisão visual completa e avaliação do extrator permanecem pendentes.
