# Aplicação web: apresentação, API e revisão local

## O que esta entrega permite fazer

A interface apresenta o problema, os resultados do experimento e três recibos reais. A pessoa pode comparar OCR e Gemini, conferir a imagem e abrir uma revisão local com histórico. Não é preciso configurar uma chave nem fazer uma nova chamada de IA.

Os indicadores usam os resultados publicados dos 20 documentos de desenvolvimento. Os três exemplos foram escolhidos para ilustrar falhas do OCR; não são uma amostra independente ou representativa.

## Testar uma imagem própria

A jornada “Testar meu recibo” permite envio temporário, OCR local, conferência e download. Instale também o extra `ocr` e inicie com `--uploads`; veja o [guia completo](uploads.md). O envio é independente da revisão persistente dos exemplos e pode ser habilitado junto de `--read-only`.

## Como abrir no computador

Na raiz do projeto:

```powershell
uv sync --locked --extra web
uv run --no-sync receipttrace serve
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000). O comando fica em execução enquanto o site estiver aberto; use Ctrl+C para encerrá-lo. Não há instalação de frontend nem processo de build para usar a aplicação. Node.js 22 ou superior é necessário somente para testes e formatação do JavaScript; não é requisito para executar a aplicação.

O banco padrão é `runs/reviews.sqlite3`, o mesmo padrão dos comandos de revisão. Para uma experiência separada, use `--database runs/minha-demonstracao.sqlite3`. Use `--port 8001` se a porta padrão estiver ocupada.

As três imagens originais e as respostas salvas fazem parte do pacote da aplicação, com atribuição CC BY 4.0. Abrir a interface não baixa o dataset completo. O download de aproximadamente 490 MB continua sendo necessário para reconstruir a amostra inteira ou reproduzir sua avaliação.

## Como usar a interface

1. Leia o problema e os resultados medidos. A economia de trabalho humano ainda não foi comprovada.
2. Abra um dos três exemplos e alterne entre OCR e Gemini. A imagem e os campos ficam juntos; o valor original não é traduzido nem recebe moeda presumida.
3. Na execução local, selecione “Abrir revisão local”. O sistema recupera ou inicia a revisão daquele documento e método.
4. Corrija os campos de totais desejados e informe responsável e motivo. Salve a correção. A tabela mantém a extração original e a anotação oficial visíveis.
5. Para concluir, registre o que foi conferido e reconheça explicitamente os cálculos não verificados ou achados. Isso não aprova pagamento ou conformidade fiscal.
6. Abra o histórico ou baixe a revisão em JSON. Uma nova correção após a conclusão reabre a revisão.

PT e EN alteram os textos e a apresentação dos indicadores, preservando o exemplo e o rascunho. Rascunhos ficam apenas na memória da página; recarregar ou fechar o navegador descarta alterações não salvas. As correções já registradas permanecem no banco e são recuperadas ao reabrir a revisão. A identificação é declarada localmente, sem login.

A tela edita cinco campos: total, subtotal, imposto, serviço e desconto. Itens são exibidos, mas não têm edição visual nem métrica de qualidade. A API e os comandos de revisão aceitam também correções de itens conforme o [contrato de revisão](review.md).

## Conflitos e estados

Cada envio inclui a versão que a pessoa conferiu. Se outra sessão alterou a revisão, a API retorna HTTP 409. A tela mantém o rascunho, bloqueia novos envios e oferece recarregar a versão atual descartando esse rascunho. É necessário conferir os valores novamente antes de prosseguir.

A interface apresenta separadamente o processamento, a verificação aritmética e a revisão. Não transforma uma resposta recebida em valor correto nem um cálculo pulado em cálculo aprovado. A comparação publicada continua medindo a extração original, mesmo após correções locais.

## Modo somente leitura

```powershell
uv run --no-sync receipttrace serve --read-only
```

Esse modo serve apresentação, exemplos e evidências. Não cria banco nem permite ler ou alterar revisões. Com `--uploads`, também permite processar novas imagens e conferir seus campos de forma transitória, sem gravar no banco. É a configuração adequada para uma demonstração pública com exemplos salvos.

O comando recusa revisão mutável com `--host 0.0.0.0`; essa vinculação exige `--read-only`. A fábrica `receipttrace.web:create_app` também inicia em somente leitura por padrão. O modo de revisão restringe os nomes de host a endereços locais e recusa origens diferentes. Esses controles não são autenticação para uma aplicação multiusuário.

Não houve publicação nem configuração de hospedagem nesta entrega. O histórico SQLite não deve depender de disco temporário de hospedagem gratuita para uso operacional.

## Organização técnica

| Arquivo ou área | Responsabilidade |
|---|---|
| `demo_catalog.py` | Conferir a integridade e fornecer os exemplos e indicadores salvos. |
| `web.py` | Validar os pedidos HTTP e conectar as rotas ao catálogo e ao `ReviewStore`. |
| `review.py` | Persistir a origem, as correções e as conclusões em transações. |
| `static/index.html`, `styles.css` | Estrutura semântica, hierarquia visual e comportamento responsivo. |
| `static/app.js` | Coordenar seleção, rascunho, ações e apresentação dos estados. |
| `static/api.js` | Centralizar chamadas HTTP e códigos de erro. |
| `static/i18n.js` | Manter o conteúdo PT-BR/EN. |
| `static/ui.js` | Criar elementos por texto e preparar correções sem converter dinheiro em ponto flutuante. |
| `webdata/` | Três imagens originais, resultados, relatórios, atribuição e checksums. |

FastAPI serve a interface e a API na mesma origem. CSS e JavaScript são locais, sem CDN ou scripts de terceiros. Dados de recibos e notas de revisão são inseridos como texto, não como HTML. Os valores `Decimal` da validação são serializados como texto na API.

A opção por módulos JavaScript sem framework está registrada na [decisão de arquitetura](architecture-web.md). O [roteiro de apresentação](case-study.md) continua orientando a evolução do produto.

## Rotas principais

| Método e rota | Uso |
|---|---|
| `GET /api/health` | Estado e modo da instância. |
| `GET /api/summary` | Indicadores do lote e disponibilidade da revisão. |
| `GET /api/examples` | Três exemplos identificados. |
| `GET /api/examples/{id}?method=ocr` | Extração, anotação da avaliação e verificações; aceita `ocr` ou `gemini`. |
| `GET /api/examples/{id}/image` | Imagem pública do exemplo permitido. |
| `POST /api/reviews` | Abrir ou recuperar revisão de um exemplo e método. |
| `GET /api/reviews/{id}` | Estado atual e histórico verificado. |
| `POST /api/reviews/{id}/corrections` | Registrar correção com versão esperada. |
| `POST /api/reviews/{id}/completion` | Registrar conclusão com versão e reconhecimentos. |
| `GET /api/reviews/{id}/export` | Baixar o estado e histórico em JSON. |
| `GET /api/evidence/{name}` | Relatórios permitidos: `ocr`, `gemini`, `comparison`, `sample` e `attribution`. |
| `GET /api/openapi.json` | Contrato OpenAPI da implementação. |

A API aceita identificadores conhecidos; não aceita caminho arbitrário de arquivo, upload ou escolha de provedor pago. Pedidos de revisão usam JSON, modelos estritos e o mesmo domínio dos comandos. Erros têm `error.code` para apresentação no idioma selecionado. Respostas de revisão usam `Cache-Control: no-store`.

Exemplo de correção: `{"expected_revision":0,"correction":{"actor":"seu-id","reason":"Conferi o total","changes":[{"path":"/total","value":"61,799"}]}}`.

Erros principais: 400 para ação recusada; 403 para modo de consulta, host ou origem não permitidos; 404 para recurso ausente; 409 para conflito de versão; 415 para conteúdo não JSON; 422 para pedido fora do contrato; 500 para falha de integridade; 503 para armazenamento indisponível.

## Verificações e reprodução

```powershell
uv run --no-sync ruff format --check .
uv run --no-sync ruff check .
uv run --no-sync mypy
uv run --no-sync pytest
node scripts/check-web.mjs
node --test tests/web/ui.test.mjs tests/web/api.test.mjs tests/web/upload-client.test.mjs
npm.cmd ci --ignore-scripts
npm.cmd run format:check
```

Os dois comandos `npm.cmd` são para PowerShell no Windows; em Linux/macOS, use `npm`. O único pacote de desenvolvimento é Prettier, fixado no `package-lock.json`. Ele padroniza HTML, CSS e JavaScript e não participa da execução da aplicação.

O ambiente de checagem de tipos inclui o extra `web`. Os testes de API são ignorados quando esse extra não está instalado. A CI separa análise estática, matrizes de dependências opcionais, verificação do pacote e testes/formatação de JavaScript; execução remota precisa ser confirmada no GitHub.

[Contrato OpenAPI exportado](contracts/web-openapi.json) · [Relatório de verificação](quality.md) · [Atribuição dos dados incluídos](../src/receipttrace/webdata/ATTRIBUTION.md)


Consulte também [segurança e tratamento de falhas](security.md) e o [relatório de revisão de 30/10/2026](reports/security-audit-2026-10-30.md).

## Ordem de apresentação

Problema → caso guiado → comparação das leituras → teste próprio ou exemplo pronto → resultados do estudo → decisões de engenharia e repositório. O resumo numérico fica junto dos resultados, depois da explicação do problema. O [estudo de caso](case-study.md) conecta a experiência aos motivos das escolhas técnicas.
