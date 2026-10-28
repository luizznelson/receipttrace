# Gemini: caminho gratuito recomendado

## Condição de custo zero
Usar chave de um projeto Gemini Developer API no **Free Tier, sem faturamento ativado**. Em 28/10/2026, a tabela oficial lista entrada e saída gratuitas para Gemini 2.5 Flash; esse é o modelo do exemplo. Cotas e disponibilidade dependem da conta. A aplicação não consegue consultar/verificar seu plano de faturamento: a confirmação é do usuário. Não use chave de projeto pago esperando que o código a transforme em gratuita.

Fontes: [preços](https://ai.google.dev/gemini-api/docs/pricing), [faturamento](https://ai.google.dev/gemini-api/docs/billing).

## Configuração
1. Abra [Google AI Studio](https://aistudio.google.com/apikey) e crie uma chave para um projeto dedicado no Free Tier. Confirme que o projeto não tem faturamento ativado. Não habilite upgrade pago para contornar cotas.
2. Na raiz do ReceiptTrace:
```powershell
uv sync --locked --extra gemini
New-Item -ItemType Directory -Path runs -Force | Out-Null
Copy-Item examples/llm-config.example.json runs/gemini-config.json
```
3. Após conferir o Free Tier, altere `free_tier_confirmed` para `true` em `runs/gemini-config.json`. Essa declaração permite a chamada real; o plano offline funciona mesmo com false.
4. Configure a chave somente no terminal:
```powershell
$receiptTraceSecret = Read-Host 'Chave Gemini' -AsSecureString
$env:GEMINI_API_KEY = [Net.NetworkCredential]::new('', $receiptTraceSecret).Password
```
Não envie a chave ao chat ou Git. `.env.example` é apenas referência; não há carregamento automático de `.env`.

## Verificação offline
```powershell
uv run --extra gemini receipttrace plan-llm --inputs data/processed/cord-inspection/inputs --config runs/gemini-config.json --output runs/gemini-plan.json
```
Esse comando não usa rede nem exige chave. Registra hashes das imagens e o prompt/esquema de saída.

## Execução e comparação
```powershell
uv run --extra gemini receipttrace extract-llm --inputs data/processed/cord-inspection/inputs --config runs/gemini-config.json --output runs/gemini-v1
uv run --extra gemini receipttrace evaluate-extraction --sample data/processed/cord-inspection --run runs/gemini-v1 --output runs/gemini-evaluation.json
uv run --extra gemini receipttrace compare-extractions --baseline docs/reports/ocr-baseline.json --candidate runs/gemini-evaluation.json --output runs/ocr-vs-gemini.json
```
Saídas devem ser novas. O exemplo espaça documentos por 15 segundos; isso não garante compatibilidade com toda cota de conta. Há uma contagem e no máximo uma inferência por documento. Se receber HTTP 429, o lote interrompe novas chamadas e registra os restantes como não processados por interrupção. Não há retentativa nem alternativa paga. Para uma primeira chamada, use uma pasta com um recibo; a comparação final exige a mesma amostra completa do OCR.

## Controles e auditoria
Configurações Gemini aceitam apenas modelos da lista gratuita verificada e preços/orçamento zero. Isso registra o custo esperado sob a condição declarada de Free Tier; não comprova faturamento da conta. A chave é enviada em cabeçalho HTTPS, não na URL. Nenhuma chave ou mensagem bruta de erro HTTP é gravada. Respostas, tokens (incluindo pensamento quando informado), modelo retornado, hashes, prompt/esquema e validações ficam no run local. API retorna formato próprio do Gemini; não depende do SDK da OpenAI.

O JSON Schema mantém subitens recursivos, com children opcional conforme restrição de ciclos do GenerateContent. Dados continuam validados por RawReceipt. `items_complete` permanece false. Bloqueios e limites de saída geram resposta incompleta/erro, nunca um resultado bem-sucedido inventado. A compatibilidade com modelo e conta reais ainda depende da primeira execução.

No plano gratuito, dados enviados podem ser usados pelo Google para melhoria de produtos. Use os recibos públicos do CORD, sem enviar documentos confidenciais. Não há ferramentas, busca, uploads persistentes pela Files API ou migração automática de faturamento nesta integração.

Referências técnicas: [imagens](https://ai.google.dev/gemini-api/docs/image-understanding), [GenerateContent](https://ai.google.dev/api/generate-content), [contagem](https://ai.google.dev/api/tokens).

## Situação atual
Adaptador e testes HTTP simulados implementados. GEMINI_API_KEY não estava configurada; não houve inferência real nem foi produzido benchmark de Gemini. A integração OpenAI permanece opcional, documentada em llm.md com configuração separada em examples/openai-config.example.json.
