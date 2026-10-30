# Revisão de segurança e falhas — 30/10/2026

## Resultado

Foram corrigidas falhas no tratamento de erros HTTP, limites de entrada, verificação dos arquivos demonstrados e recuperação da interface após uma confirmação perdida. Uma dependência com alertas conhecidos foi atualizada. Nenhuma evidência original de extração, imagem ou avaliação foi recalculada ou alterada.

O escopo foi revisão do código, testes automatizados, consulta de dependências e um cenário de falha simulado no navegador. Não foi um teste de invasão, certificação de segurança ou avaliação de uma implantação pública.

## Problemas confirmados e correções

| Problema | Correção e evidência |
| --- | --- |
| Erros inesperados sem contrato JSON estável | Camada ASGI devolve erro genérico e ID; testes de RuntimeError, ValueError, TimeoutError de processamento e PermissionError confirmam ausência do segredo sintético na resposta e no log da aplicação. |
| Respostas antecipadas sem os mesmos cabeçalhos | CSP, nosniff, no-referrer, no-store na API e ID também nos erros de origem, host, tamanho, modo de leitura e roteamento. |
| Entrada de escrita sem limite explícito | 256 KiB e 10 s antes da rota; testes incluem Content-Length incorreto, partes sem tamanho declarado, cliente lento e desconexão. |
| ValueError e PermissionError genéricos classificados como erro de usuário | Exceções de domínio específicas; falhas inesperadas retornam 500. Erros de recebimento do corpo são distinguidos de timeouts posteriores de processamento. |
| Arquivos alterados após a inicialização poderiam ser entregues | Conferência dos arquivos solicitados; testes removem ou adulteram imagens, extrações e relatórios em cópias temporárias. A atribuição também passou a integrar checksums.json. |
| Escrita sem confirmação poderia ser reenviada sem conferência | Timeout no navegador, distinção de falha de rede e resposta inválida, preservação do rascunho e bloqueio até recarregar. Testes verificam que não há repetição automática. |
| Alertas de dependência no Pillow 12.3.0 | Atualização para 13.0.0 no contrato e lock. Consulta posterior sem alertas conhecidos nas dependências verificadas. |

O pip-audit inicial retornou vários registros de avisos no Pillow, alguns com identificadores equivalentes. Isso não foi interpretado como uma contagem de vulnerabilidades distintas. Um aviso consultado diretamente foi o [GHSA-4558-3h8r-v8xp publicado pelo mantenedor](https://github.com/python-pillow/Pillow/security/advisories/GHSA-4558-3h8r-v8xp), que identifica 13.0.0 como versão corrigida. Não foi demonstrada exploração na aplicação.

## Verificações concluídas

- Python 3.14.3, Pillow 13.0.0, ambiente isolado `runs/security-env`: **198 testes passaram**, incluindo 25 novos testes de segurança.
- Node: **21 testes passaram**, incluindo 13 novos testes do cliente HTTP.
- Ruff, formatação Python, mypy em 17 módulos, sintaxe JavaScript e Prettier: aprovados.
- Wheel gerado e conferido: 50 arquivos de evidência com checksum, arquivos da interface e atribuição presentes; sem `.env` nem banco SQLite.
- pip-audit 2.10.1, dependências fixadas com todos os extras e dependências de desenvolvimento aplicáveis ao ambiente da consulta: nenhum alerta conhecido após a atualização.
- npm audit com o package-lock atual: nenhum alerta conhecido.
- `git diff --check`: sem erros. Entre arquivos de ambiente rastreados, somente `.env.example`; bancos e credenciais locais não foram incluídos. Não houve auditoria do histórico completo.
- Histórico de resultados anteriores preservado. A contagem de 49 arquivos no relatório web anterior descreve aquela entrega; esta revisão inclui a atribuição no checksum e passa a 50.

## Cenário no navegador

Em servidor separado na porta 8010 e banco exclusivo de QA, um adaptador externo ao produto simulou resposta 500 **depois** de uma correção efetivamente gravada. A interface manteve o rascunho, informou que o salvamento era incerto e desabilitou novas alterações. Ao selecionar recarregar, apresentou a versão 1 e o histórico `62,000 → 61,799`, sem repetir a correção. Responsável e motivo identificavam explicitamente um teste automatizado. O servidor de QA foi encerrado; o servidor habitual não foi interrompido.

Esse teste verifica a recuperação do fluxo; não representa uma falha real em produção nem uma medição de revisão humana. O timeout de rede foi exercitado pelos testes JavaScript; no navegador, a falha foi injetada como resposta 500 após a gravação.

## Reprodução

Na pasta do projeto, com o servidor habitual encerrado se estiver usando o mesmo ambiente:

```powershell
uv sync --locked --all-extras
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
npm.cmd ci --ignore-scripts
npm.cmd test
npm.cmd run format:check
node scripts/check-web.mjs
uv build --wheel --out-dir runs/security-wheel-replay
uv run --no-sync python scripts/check-wheel.py runs/security-wheel-replay
uv export --locked --all-extras --no-hashes --no-emit-project --format requirements-txt --output-file runs/security-requirements-fixed.txt
uvx --from pip-audit==2.10.1 pip-audit --requirement runs/security-requirements-fixed.txt --no-deps --disable-pip --format json --output runs/python-security-audit-fixed.json --progress-spinner off
npm.cmd audit --json --registry=https://registry.npmjs.org
```

O arquivo exportado contém as dependências transitivas fixadas, por isso a consulta usa `--no-deps --disable-pip` sem instalar o projeto no ambiente do auditor. Os arquivos integrais das consultas locais ficam em `runs/`, fora do Git. O [resumo estruturado](security-audit-2026-10-30.json) registra versões e contagens sem incluir dados de revisão ou chaves.

Os resultados são locais; a execução remota da CI ainda deve ser confirmada no GitHub. Os [limites e requisitos antes de publicar](../security.md) permanecem aplicáveis. O servidor que já estava aberto precisa ser reiniciado com as dependências atualizadas para incorporar esta entrega.
