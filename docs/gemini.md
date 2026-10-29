# Gemini gratuito: configuração e uso

## Estado atual
Integração avaliada nos 20 recibos da amostra de desenvolvimento com Gemini 3.5 Flash-Lite, raciocínio mínimo e API Interactions. [Resultados, evidências e reprodução sem chamadas de API](reports/gemini-development-20.md). A amostra pertence ao treino e não é teste reservado. O [teste isolado anterior](reports/gemini-api-audit.md) documenta a correção da integração.

## Condição de custo zero
Use chave de projeto Gemini Developer API no Free Tier, sem faturamento ativado. O modelo do exemplo está listado como gratuito na [tabela oficial](https://ai.google.dev/gemini-api/docs/pricing), consultada em 28/10/2026. Nem todo projeto é elegível; confirme o plano no AI Studio. Não há upgrade de cobrança nem alternativa automática para provedor pago.

## Configuração por arquivos
1. Copie `.env.example` para `.env`, se ainda não existir, e preencha somente a chave:
```dotenv
GEMINI_API_KEY=sua_chave_aqui
```
O arquivo é lido automaticamente e está fora do Git. O ambiente do processo tem prioridade. Não há busca em pastas superiores nem expansão de variáveis. Nunca envie a chave ao chat.

2. Prepare o ambiente e a configuração não secreta:
```powershell
uv sync --locked --extra gemini
New-Item -ItemType Directory -Path runs -Force | Out-Null
Copy-Item examples/llm-config.example.json runs/gemini-config.json
```
Não sobrescreva uma configuração local já ajustada. Após conferir o Free Tier, defina `free_tier_confirmed: true` no JSON. Para a configuração local deste usuário, a confirmação já foi fornecida e um arquivo foi preparado se não existia.

O exemplo seleciona `gemini-3.5-flash-lite`, `thinking_level: minimal`, valores de preço/orçamento zero, no máximo 20 documentos e intervalo de 15 segundos. Essas cotas locais não garantem capacidade disponível na conta.

## Planejar sem rede
```powershell
uv run --extra gemini receipttrace plan-llm --inputs data/processed/cord-inspection/inputs --config runs/gemini-config.json --output runs/gemini-plan.json
```
Verifica imagens e registra hashes, prompt, esquema e configuração. Não exige chave nem confirmação para enviar chamadas, pois não usa rede.

## Executar e avaliar
```powershell
uv run --extra gemini receipttrace extract-llm --inputs data/processed/cord-inspection/inputs --config runs/gemini-config.json --output runs/gemini-v1
uv run --extra gemini receipttrace evaluate-extraction --sample data/processed/cord-inspection --run runs/gemini-v1 --output runs/gemini-evaluation.json
uv run --extra gemini receipttrace compare-extractions --baseline docs/reports/ocr-baseline.json --candidate runs/gemini-evaluation.json --output runs/ocr-vs-gemini.json
```
Saídas precisam ser novas. A comparação requer a mesma amostra completa. Para teste isolado, use uma pasta com uma imagem e não compare seu resultado ao relatório agregado de 20 documentos.

## Contrato da API
POST `/v1beta/interactions`, imagem inline base64, `response_format` JSON Schema, `generation_config.thinking_level` explícito e `store=false`. Texto final vem de `steps/model_output`; blocos de pensamento não são tratados como resposta. Não há ferramentas ou navegação.

A gramática remota omite limites grandes de arrays e permite filhos recursivos opcionais; os limites de 1.000 itens e 100 filhos são impostos localmente por Pydantic. O ID é local e a completude de itens permanece false. Null não vira zero.

A pré-contagem usa countTokens na representação GenerateContent do mesmo conteúdo/esquema. O uso efetivo é o informado pela Interactions, pode diferir da pré-contagem e é preservado separadamente, incluindo tokens de pensamento. Os manifestos registram as configurações e hashes para reprodução; não são faturas nem comprovantes de plano gratuito.

## Falhas e dados
Cota 429, projeto inelegível, modelo indisponível e esquema excessivamente complexo têm diagnóstico específico e interrompem novas chamadas. Timeouts sem uso conhecido também interrompem o lote. Não há retentativas automáticas. Execuções locais e respostas ficam em `runs/`, fora do Git.

No plano gratuito, o Google pode usar os dados para melhoria de produtos. Use os recibos públicos do CORD; não envie documentos confidenciais. `store=false` controla o armazenamento da interação, sem prometer ausência de toda retenção ou processamento pelo provedor.

Referências: [Interactions](https://ai.google.dev/gemini-api/docs/interactions-overview), [pensamento](https://ai.google.dev/gemini-api/docs/thinking), [esquemas](https://ai.google.dev/gemini-api/docs/structured-output). OpenAI permanece opcional em llm.md.
