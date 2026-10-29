# OpenAI: integração paga opcional

**Caminho recomendado: [Gemini Free Tier](gemini.md).** Esta página documenta apenas o provedor OpenAI opcional; seus preços e requisitos não se aplicam ao Gemini.

## Estado
Adaptador implementado para OpenAI Responses API, imagens e saída JSON estruturada. Não foi executada inferência paga: OPENAI_API_KEY não estava configurada. Não há alegação de acurácia, custo real ou superioridade em relação ao OCR.

Não foi escolhido modelo padrão ou presumido acesso da conta. Use um modelo disponível com visão, Structured Outputs e contagem de tokens; prefira snapshot estável e registre preços atuais correspondentes antes da execução.

## Configuração explícita
```powershell
uv sync --locked --extra llm
New-Item -ItemType Directory -Path runs -Force | Out-Null
Copy-Item examples/openai-config.example.json runs/llm-config.json
```
Edite `runs/llm-config.json`: substitua todos os SET_ por modelo, teto em USD e tarifas por milhão de tokens. Atualize pricing_as_of. Os placeholders falham antes de qualquer envio. Não inclua a chave nesse arquivo.

A credencial opcional OpenAI também pode ficar no arquivo `.env` da raiz:
```dotenv
OPENAI_API_KEY=sua_chave_aqui
```
O arquivo é lido automaticamente, sem alterar o ambiente global. Variáveis existentes no processo têm prioridade. Não coloque segredos em JSON, chat ou Git. Para Gemini use GEMINI_API_KEY e as instruções em gemini.md.

## Planejamento sem rede
```powershell
uv run --extra llm receipttrace plan-llm --inputs data/processed/cord-inspection/inputs --config runs/llm-config.json --output runs/llm-plan.json
```
Verifica imagens, hashes, prompt, esquema e número máximo de solicitações. Não requer chave, não envia imagens e não estima custo sem contagem do provedor. Se quiser testar apenas um documento, use um diretório com essa única imagem e ajuste max_requests; não compare essa seleção com o benchmark completo de 20 documentos.

## Execução com envio e possível cobrança
Após conferir configuração e orçamento:
```powershell
uv run --extra llm receipttrace extract-llm --inputs data/processed/cord-inspection/inputs --config runs/llm-config.json --output runs/llm-v1
uv run --extra llm receipttrace evaluate-extraction --sample data/processed/cord-inspection --run runs/llm-v1 --output runs/llm-evaluation.json
uv run --extra llm receipttrace compare-extractions --baseline docs/reports/ocr-baseline.json --candidate runs/llm-evaluation.json --output runs/ocr-vs-llm.json
```
O comando antigo evaluate-ocr continua como alias. Comparação exige o mesmo manifesto de amostra, IDs, imagens e denominadores. Não há comparação real enquanto não houver execução real de IA.

## Orçamento e limites
Para cada documento, o adaptador envia imagem, prompt e esquema ao endpoint de contagem; somente após contar e reservar o custo segue para inferência. A reserva usa tokens de entrada contados e o máximo de saída configurado, nas tarifas informadas, sem descontar cache. Reservas anteriores não são liberadas para aumentar o lote. Número de imagens não pode exceder max_requests; há no máximo uma inferência por imagem e até uma contagem por imagem, sem retentativas automáticas.

Falha da contagem ou reserva insuficiente impede a inferência daquele documento. Timeout de inferência ou ausência de uso conhecido interrompe novas solicitações e mantém a reserva, pois cobrança pode ter ocorrido. Uso conhecido maior que a reserva é registrado e interrompe solicitações futuras. Recusas e respostas incompletas preservam os metadados de uso quando disponíveis.

O teto é um controle de estimativa com tarifas e contagens declaradas, não uma garantia contratual de faturamento: preços errados/desatualizados, condições especiais da conta, diferenças de contagem ou cobranças não representadas podem divergir. Configure também controles de gastos no provedor. Custos do endpoint de contagem não são presumidos gratuitos nem estimados pelo projeto; confirmar a política do provedor antes do uso.

## Contrato e segurança
Imagem é dado não confiável, não instrução. Não há ferramentas, busca, links externos ou ações na integração. O prompt versionado proíbe completar valores por cálculo, confundir troco/pagamento com total e presumir moeda. Campo ilegível permanece null. O ID é atribuído localmente e items_complete permanece false mesmo que a resposta diga true. Esquema de transporte usa todos os campos obrigatórios com null permitido, additionalProperties=false e validação local adicional.

O extrator recebe somente diretório de imagens. Gabaritos não são enviados. Imagens são enviadas em memória, sem redimensionamento local; payload/base64 e chave não entram nos relatórios. store=false é enviado para geração, mas isso não promete ausência de retenção por todas as políticas do provedor. Apenas dados públicos/autorizados devem ser usados.

## Auditoria
Resultados locais preservam resposta do provedor, ID, modelo retornado, tokens, estimativa de custo, hash de imagem, validação, duração, prompt/esquema/configuração e versões. Manifesto inclui commit, alterações locais, hashes de código/lock e reservas acumuladas. Exceções do provedor são registradas apenas por classe, para não copiar corpos que possam conter dados/credenciais. `runs/` e credenciais não entram no Git.

Latência de IA inclui contagem remota, inferência e validação; difere do OCR local. Compare qualidade nos mesmos documentos, mas interprete os tempos com esses escopos explícitos. Estimativas de custo não são faturas. Cache não é controlado pelo projeto; o custo estimado usa tarifa de entrada sem desconto.

## Referências oficiais consultadas
- [Imagens na Responses API](https://developers.openai.com/api/docs/guides/images-vision?api-mode=responses)
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
- [Contagem de entrada](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count)
- [Preços atuais](https://developers.openai.com/api/docs/pricing)

Os testes usam provedores sintéticos e HTTPX MockTransport: nenhum teste depende de rede, chave real ou inferência paga. Compatibilidade com um modelo/conta reais só será confirmada com uma execução autorizada.
