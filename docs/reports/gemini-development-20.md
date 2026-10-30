# Gemini versus OCR: 20 recibos reais — 29/10/2026

## O que foi observado

O Gemini recuperou corretamente cinco totais que o OCR havia errado ou deixado sem resposta. Nos campos anotados desta amostra, acertou todos os totais, subtotais e impostos que podiam ser conferidos. O ganho de qualidade veio com maior tempo de processamento: mediana de 8,33 segundos por recibo, contra 1,04 segundo do OCR.

Esse resultado apoia a continuidade da demonstração com IA e revisão humana. Ainda não comprova economia de trabalho em uma empresa nem desempenho em documentos novos. A amostra é pequena e já foi usada no desenvolvimento.

## Como a comparação foi feita

Amostra determinística de desenvolvimento do CORD v2: 20 imagens do primeiro arquivo de treino, semente 42. Mesmos documentos, imagens e campos elegíveis do OCR original. O extrator recebe somente as imagens; os gabaritos são lidos depois pelo avaliador independente. Sem ajuste do prompt durante este lote e sem retentativas automáticas. Um dos documentos já havia sido usado no teste isolado de integração.

Modelo solicitado: `gemini-3.5-flash-lite`, API Interactions, `thinking_level=minimal`, `store=false`, limite de saída 4.096 tokens, intervalo de 15 segundos entre documentos. Configuração, prompt e esquema completos estão no [manifesto preservado](evidence/gemini-development-20/manifest.json).

## Resultados por campo

Os dois métodos processaram os mesmos 20 documentos. O Gemini concluiu as 20 extrações sem falha técnica ou resposta vazia. Concluir uma extração significa receber uma resposta válida no formato esperado; não significa que todos os campos estejam corretos.

A tabela compara os valores extraídos com as anotações oficiais. Cada número é conferido após normalização monetária explícita, sem tolerância. Se um documento falhar, ele continua no cálculo dos campos que têm referência válida.

| Informação | Documentos com referência válida | Acertos do OCR | Acertos do Gemini | Valores errados do Gemini | Sem resposta do Gemini |
|---|---:|---:|---:|---:|---:|
| Total | 19 | 14 | 19 | 0 | 0 |
| Subtotal | 14 | 9 | 14 | 0 | 0 |
| Imposto | 11 | 7 | 11 | 0 | 0 |
| Serviço | 1 | 1 | 1 | 0 | 0 |
| Desconto | 0 | 0 | 0 | 0 | 0 |

Não foi calculada uma nota geral de acerto do recibo. Campos sem anotação não são negativos; serviço tem apenas uma referência válida e desconto não tem referência válida. Métricas de itens ainda não foram implementadas. [Resultados completos e valores por documento](gemini-development-20.json) e [comparação gerada pelo avaliador](ocr-vs-gemini-development-20.json).

## Tempo de processamento e custo estimado

A mediana, ou p50, descreve o tempo central da amostra. O p95 indica o tempo na posição correspondente a 95% dos documentos ordenados por duração. Esses indicadores ajudam a distinguir o tempo típico das respostas mais demoradas.

Gemini: mediana de 8,333 s e p95 de 22,524 s. OCR: mediana de 1,043 s e p95 de 1,673 s. Percentis pelo método nearest rank. Gemini inclui pré-contagem remota de tokens, inferência e validação; OCR executa localmente em CPU. As medições por documento excluem a pausa de 15 segundos entre documentos e a gravação da saída. Não representam latência em hospedagem gratuita.

O provedor informou o uso das 20 respostas. Tokens são as unidades usadas pela API para contabilizar o processamento: 26.332 tokens de entrada e 3.689 tokens de saída normalizados (total menos entrada, incluindo pensamento quando houver). Uso por resposta permanece na evidência original. A pré-contagem é separada do uso efetivo. Custo estimado conhecido: USD 0, com taxas zero e projeto Free Tier confirmado pelo usuário, sem faturamento ativado. Isso não é fatura nem verificação do plano pela API. Limites do plano gratuito continuam sujeitos à conta. Computação e hospedagem não foram precificadas.

## Campos sem referência e revisão visual

Não houve valor errado nem campo sem resposta entre os que tinham referência numérica válida neste lote. Isso não comprova que todos os itens ou campos não anotados estejam corretos.

No documento `cord-train-shard0-row0173`, Gemini extraiu desconto `-38,500`, mas o campo não está anotado no gabarito. Uma inspeção visual pontual nesta etapa confirmou o valor impresso ao lado de 10%. O caso permanece `unannotated_prediction`, fora das métricas; o gabarito oficial não foi alterado. Não houve revisão visual integral dos 20 documentos nesta etapa.

## O que ainda não foi verificado

As 76 verificações locais retornaram `skipped`, por ausência de componentes exigidos ou itens não certificados como completos. Nenhuma relação aritmética foi efetivamente aprovada neste lote. Isso é uma limitação de cobertura das regras atuais, mesmo com os acertos nos campos anotados; ausência de alerta não certifica consistência do recibo. A próxima etapa de revisão humana deve tornar esse estado visível.

## Exemplos do ganho em relação ao OCR

Os valores abaixo preservam a escrita da saída original. “Sem resposta” significa que o OCR não encontrou um candidato aceito pelas regras.

- `cord-train-shard0-row0006`: total `61,799` correto; OCR extraiu `62,000`, um valor incorreto.
- `cord-train-shard0-row0057`: total `39,000` correto; OCR ficou sem resposta.
- `cord-train-shard0-row0059`: total `25,000` correto; OCR extraiu `22,727`, um valor incorreto.
- `cord-train-shard0-row0062`: total `3.600.000` correto; OCR ficou sem resposta.
- `cord-train-shard0-row0173`: total `346,500` correto; OCR ficou sem resposta.

## Como auditar e recalcular os resultados

É possível conferir as métricas usando as respostas salvas, sem fazer novas chamadas de IA. O manifesto é o registro que relaciona os arquivos, suas configurações e seus hashes, usados para detectar alterações.

Os arquivos de extração e manifestos originais foram copiados sem alteração para [evidência Gemini](evidence/gemini-development-20/manifest.json) e [evidência OCR](evidence/ocr-baseline/manifest.json). Incluem saída original, validação, tempos, configuração disponível, hashes de imagem/código/lock e commit observado. Havia alterações locais no código durante a execução; por isso, o commit sozinho não identifica todo o código executado. Os hashes de fonte registram essa diferença. Nenhuma chave foi publicada. Na avaliação original, imagens e gabaritos ficaram fora do Git. A [aplicação web posterior](../web.md) inclui três imagens originais com atribuição; os arquivos de gabarito continuam fora do repositório.

As evidências publicadas de ambas as abordagens foram reavaliadas contra a amostra local verificada, sem chamar a API. O relatório Gemini foi reproduzido com os mesmos bytes. No OCR, métricas, valores por documento, hashes de origem e tempos foram reproduzidos sem diferença; apenas os textos descritivos de latência e limitações diferem porque o avaliador foi atualizado desde o relatório original. O relatório histórico foi preservado.

```powershell
uv sync --locked --extra gemini
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
uv run receipttrace evaluate-extraction --sample data/processed/cord-inspection --run docs/reports/evidence/gemini-development-20 --output runs/gemini-replay.json
uv run receipttrace evaluate-extraction --sample data/processed/cord-inspection --run docs/reports/evidence/ocr-baseline --output runs/ocr-replay.json
uv run receipttrace compare-extractions --baseline runs/ocr-replay.json --candidate runs/gemini-replay.json --output runs/comparison-replay.json
```

Use saídas novas. Se a amostra já existir, apenas verifique-a. Uma nova aquisição preserva IDs e hashes dos arquivos, mas altera a data do manifesto e seu hash; isso não altera as métricas. O [manifesto publicado da amostra original](cord-inspection.manifest.json) permite conferir a proveniência desta execução. Reavaliação dos arquivos salvos é determinística sob o mesmo avaliador; nova inferência remota pode produzir resultados diferentes. Para nova inferência, siga o [guia Gemini](../gemini.md), usando outra pasta de saída.

## Onde o resultado se aplica e origem dos dados

Amostra pequena de treino, já usada no desenvolvimento; não é teste reservado. O provedor pode ter tido exposição ao CORD durante treinamento. Não comprova generalização, documentos fiscais brasileiros, conferência nota versus pedido ou qualidade de todos os itens. Anotações incompletas não são corrigidas para melhorar o resultado. Valores extraídos em campos não anotados exigem inspeção humana; não são automaticamente alucinações.

Fonte: [CORD, autores originais](https://github.com/clovaai/cord), [CORD v2 público](https://huggingface.co/datasets/naver-clova-ix/cord-v2), revisão `7f0115a4b758a71d6473b8d085751692da2fef98`, CC BY 4.0. As saídas publicadas são derivadas desses recibos; não incluem imagens. A licença dos dados é independente da licença do código.

## Verificações da execução original

113 testes aprovados; Ruff e mypy aprovados. Integridade dos 20 documentos verificada, avaliação independente e comparação concluídas, reprodução das evidências publicadas conferida. Assistência de IA usada na execução e documentação, sujeita à revisão do responsável pelo projeto. Sem CI remota, commit, push ou deploy nesta etapa.
