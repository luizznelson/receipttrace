# Gemini: configuração e execução

## Resultado e finalidade

O Gemini é o caminho de IA avaliado no projeto. Nos 20 recibos de desenvolvimento, acertou os 19 totais que tinham referência válida. A amostra é pequena e pertence ao treino; esse resultado ainda não comprova desempenho em documentos novos. Veja o [relatório completo](reports/gemini-development-20.md).

Este guia explica como configurar a chave, extrair novas respostas e preservar evidências. Para apenas conferir as métricas publicadas, use as respostas salvas conforme o relatório: não é preciso chave nem chamada de API.

## Condição para usar o plano gratuito

Use uma chave de projeto Gemini Developer API no Free Tier, sem faturamento ativado. O modelo do exemplo constava como gratuito na [tabela oficial](https://ai.google.dev/gemini-api/docs/pricing), consultada em 28/10/2026. Elegibilidade e cotas dependem da conta e devem ser conferidas no AI Studio. O programa não ativa faturamento e não troca automaticamente para um provedor pago.

## 1. Salvar a chave em um arquivo

Copie `.env.example` para `.env`, caso ainda não exista, e preencha:

```dotenv
GEMINI_API_KEY=sua_chave_aqui
```

O arquivo `.env` fica na raiz do projeto, é lido automaticamente e está fora do Git. Se uma variável já estiver definida no processo, ela tem prioridade. A leitura não busca pastas superiores nem expande outras variáveis. Não publique a chave.

## 2. Preparar a configuração da execução

```powershell
uv sync --locked --extra gemini
New-Item -ItemType Directory -Path runs -Force | Out-Null
```

Se `runs/gemini-config.json` ainda não existir, copie o exemplo:

```powershell
Copy-Item examples/llm-config.example.json runs/gemini-config.json
```

Preserve uma configuração local já ajustada. Abra o JSON e defina `free_tier_confirmed` como `true` somente depois de conferir o plano gratuito da conta. Essa confirmação local não é uma verificação automática de faturamento.

| Parâmetro do exemplo | Finalidade |
|---|---|
| `model: gemini-3.5-flash-lite` | Modelo usado na avaliação real publicada. |
| `thinking_level: minimal` | Nível de raciocínio escolhido para a extração. |
| `max_requests: 20` | Limita o número de documentos do lote. |
| `min_interval_seconds: 15` | Adiciona uma pausa entre documentos. |
| `max_output_tokens: 4096` | Limita a saída solicitada por inferência. |
| Tarifas e orçamento zero | Restringem a configuração a esta modalidade gratuita; não comprovam elegibilidade da conta. |

Esses controles locais não garantem que haverá cota disponível no provedor. Os arquivos de configuração não recebem a chave.

## 3. Conferir o plano sem enviar imagens

Prepare a amostra conforme o [guia de desenvolvimento](development.md) e execute:

```powershell
uv run --extra gemini receipttrace plan-llm --inputs data/processed/cord-inspection/inputs --config runs/gemini-config.json --output runs/gemini-plan.json
```

O comando verifica as imagens e registra hashes, prompt, esquema e configuração. Não usa rede, não exige chave e não faz contagem remota de tokens.

## 4. Extrair e avaliar

```powershell
uv run --extra gemini receipttrace extract-llm --inputs data/processed/cord-inspection/inputs --config runs/gemini-config.json --output runs/gemini-v1
uv run --extra gemini receipttrace evaluate-extraction --sample data/processed/cord-inspection --run runs/gemini-v1 --output runs/gemini-evaluation.json
uv run --extra gemini receipttrace compare-extractions --baseline docs/reports/ocr-baseline.json --candidate runs/gemini-evaluation.json --output runs/ocr-vs-gemini.json
```

Use saídas novas. A extração envia imagens públicas ao provedor; a avaliação posterior compara as respostas com as anotações locais. A comparação exige a mesma amostra completa. Um teste isolado de uma imagem não deve ser comparado ao resultado agregado de 20 documentos.

## Detalhes técnicos da integração

A geração usa `POST /v1beta/interactions`, imagem inline em base64, `response_format` com JSON Schema, `generation_config.thinking_level` explícito e `store=false`. O texto final é lido de `steps/model_output`; blocos de pensamento não são usados como resposta. Não são habilitadas ferramentas ou navegação.

O esquema remoto permite filhos recursivos opcionais e omite limites grandes de arrays para evitar a rejeição por complexidade documentada na [auditoria](reports/gemini-api-audit.md). Pydantic mantém os limites locais de 1.000 itens e 100 filhos. O ID é atribuído localmente, `items_complete` permanece `false` e `null` não é convertido em zero.

A pré-contagem usa `countTokens` com a representação GenerateContent do conteúdo e do esquema. O uso efetivo vem da Interactions, é preservado separadamente e pode diferir dessa estimativa. A contagem normalizada de saída inclui tokens de pensamento quando houver. Manifestos registram configurações e hashes; não são faturas nem comprovantes de plano gratuito.

## Como as falhas são tratadas

Cota HTTP 429, projeto inelegível, modelo indisponível e esquema excessivamente complexo interrompem novas chamadas. Um timeout sem uso conhecido também interrompe o lote. Não há retentativas automáticas. Documentos não processados continuam registrados como erro para que a falha não desapareça da avaliação.

Execuções de trabalho ficam em `runs/`, fora do Git. Cópias revisadas dos resultados publicados ficam em `docs/reports/evidence/`. Credenciais permanecem excluídas.

## Dados enviados e referências

Use os recibos públicos do CORD. No plano gratuito, o Google pode usar dados para melhoria de produtos. `store=false` controla o armazenamento da interação, mas não promete ausência de toda retenção pelo provedor. Não envie documentos confidenciais por este fluxo.

Referências consultadas na implementação: [Interactions](https://ai.google.dev/gemini-api/docs/interactions-overview), [raciocínio](https://ai.google.dev/gemini-api/docs/thinking), [saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output). O [adaptador OpenAI](llm.md) é opcional e não faz parte dos resultados medidos aqui.
