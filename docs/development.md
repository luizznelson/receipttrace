# Ambiente, dados e verificações locais

## Preparar o ambiente

Use Python 3.14 e uv. O arquivo `uv.lock` fixa as versões das dependências. Na raiz do projeto:

```powershell
uv sync --locked --extra web
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

Ruff verifica formatação e estilo; mypy verifica tipos; pytest executa os testes. Os testes usam exemplos sintéticos identificados e as evidências públicas incluídas, sem baixar o CORD ou fazer chamadas de IA. O extra `web` fornece as bibliotecas para checar os tipos e executar os testes da API. A medição da qualidade dos extratores é uma etapa separada.

Para gerar novas extrações, instale a dependência opcional indicada no [guia OCR](ocr.md) ou no [guia Gemini](gemini.md). Reavaliar as respostas já publicadas não exige uma chave de API.

## Obter a amostra real

```powershell
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
```

O primeiro comando baixa aproximadamente 490 MB, confere o SHA-256 oficial e seleciona 20 documentos do primeiro arquivo de treino com semente 42. Não baixa validação ou teste. A revisão e o hash da origem estão fixados no código; atualizar a fonte exige uma mudança explícita.

| Caminho | Conteúdo |
|---|---|
| `data/raw/cord/download.json` | Registro da aquisição |
| `data/processed/cord-inspection/manifest.json` | Origem, IDs, hashes e seleção da amostra |
| `data/processed/cord-inspection/inputs/` | Imagens recebidas pelos extratores |
| `data/processed/cord-inspection/reference/` | Anotações lidas somente pelo avaliador |

Se a amostra já existir, use `verify-sample`. Para repetir a preparação, escolha outra saída com `--output data/processed/cord-repeat`. O arquivo original já verificado é reutilizado. Os IDs e os hashes dos documentos permanecem iguais; datas e hash do manifesto podem mudar.

Uma corrupção de arquivo gera erro explícito. Um download interrompido não é apresentado como concluído; a próxima tentativa recomeça o download. O manifesto ajuda a detectar alterações, mas não é uma assinatura digital.

## Conferir os resultados publicados

Siga os comandos do [relatório comparativo](reports/gemini-development-20.md). Eles avaliam os arquivos salvos e não enviam novas solicitações ao Gemini. Use saídas novas para preservar o histórico.

Os recibos foram avaliados como amostra de desenvolvimento. A revisão visual integral, a pesquisa de duplicatas entre divisões e a avaliação em teste reservado continuam pendentes.

## Origem e publicação dos dados

Fonte: [CORD v2](https://huggingface.co/datasets/naver-clova-ix/cord-v2), dos [autores do CORD](https://github.com/clovaai/cord), sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

As imagens são preservadas byte a byte. As anotações são serializadas novamente em JSON sem alteração de conteúdo. O dataset completo, os gabaritos e as execuções de trabalho ficam fora do Git. A aplicação inclui três imagens originais com atribuição para a demonstração independente de download. Relatórios e cópias revisadas de resultados derivados ficam em `docs/reports/`, com atribuição da origem.

## Verificações do frontend

Com Node.js 22 ou superior, execute `node scripts/check-web.mjs` e `node --test tests/web/ui.test.mjs tests/web/api.test.mjs tests/web/upload-client.test.mjs`. Os testes nativos não exigem pacotes JavaScript. Para conferir a formatação, instale o Prettier fixado com `npm.cmd ci --ignore-scripts` e execute `npm.cmd run format:check` (use `npm` em Linux/macOS). Para uso da aplicação, siga o [guia web](web.md).
