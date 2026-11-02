# Como verificar a qualidade

Qualidade de extração, correção do software e usabilidade são verificadas separadamente.

## Qualidade da extração

O [relatório do experimento](reports/gemini-development-20.md) mostra a comparação em 20 recibos públicos. As [respostas originais](reports/evidence/) e os manifestos permitem recalcular os resultados sem nova chamada de IA. Testes automatizados não são uma medida de acurácia do OCR ou do Gemini.

## Correção do software

Os testes cobrem políticas monetárias, componentes ausentes, falhas de provedores, integridade, transações, conflitos de revisão, limites de imagem, timeout com encerramento do processo, JSON inválido e recuperação do cliente HTTP. O CSV protege células que poderiam ser interpretadas como fórmulas em planilhas.

Na raiz do projeto:

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
uv build --wheel --out-dir runs/package-check
uv run --no-sync python scripts/check-wheel.py runs/package-check
```

A CI em `.github/workflows/ci.yml` executa as verificações por área e dependências opcionais; sua execução remota precisa ser confirmada no GitHub. Não é uma certificação de segurança. A [consulta de dependências e correções de segurança](reports/security-audit-2026-10-30.md) mantém evidências próprias e deve ser renovada ao atualizar pacotes.

## Experiência e acesso

A conferência no navegador deve incluir: caso pronto sem OCR habilitado, correção com motivo, revalidação, CSV e JSON, troca PT-BR/EN preservando o rascunho, erro de formato, indisponibilidade com nova consulta e ausência de rolagem horizontal em tela pequena.

A leitura salva do exemplo é identificada como tal: carregá-la não significa executar novo OCR nem medir acurácia. Novos recibos usam OCR local com limites e não são incorporados ao estudo. A revisão persistente dos exemplos permanece bloqueada no modo público.

Consulte o [guia de segurança](security.md) para limites de autenticação, hashes e infraestrutura. Uso com várias pessoas, implantação pública, memória/CPU na hospedagem e avaliação de produtividade continuam pendentes.

## Verificação local da apresentação atual

Em 30/10/2026, a suíte completa passou com 233 testes Python e 29 testes JavaScript. Depois da leitura por IA no envio, a suíte local passou com 262 testes Python e 31 testes JavaScript; Ruff, mypy em 22 módulos, sintaxe JavaScript e Prettier foram conferidos. Os alvos relativos dos links Markdown também foram verificados. São resultados locais, sem afirmar execução remota da CI ou teste de invasão.

A apresentação reorganizada foi conferida no navegador: exemplo salvo identificado, política numérica correta, correção com motivo, revalidação, download CSV com conteúdo verificado e troca de idioma preservando valores. Em viewport de 375 × 812, a largura observada do documento foi 360 pixels, sem rolagem horizontal. Os 19 documentos intermediários retirados estavam no Git e tiveram recuperação verificada antes da limpeza. Os resultados e as respostas originais do experimento permaneceram inalterados.
