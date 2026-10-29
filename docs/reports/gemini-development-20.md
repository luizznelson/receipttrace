# Gemini versus OCR: 20 recibos reais — 29/10/2026

## Experimento
Amostra determinística de desenvolvimento do CORD v2: 20 imagens do primeiro arquivo de treino, semente 42. Mesmos documentos, imagens e campos elegíveis do OCR original. O extrator recebe somente as imagens; os gabaritos são lidos depois pelo avaliador independente. Sem ajuste do prompt durante este lote e sem retentativas automáticas. Um dos documentos já havia sido usado no teste isolado de integração.

Modelo solicitado: `gemini-3.5-flash-lite`, API Interactions, `thinking_level=minimal`, `store=false`, limite de saída 4.096 tokens, intervalo de 15 segundos entre documentos. Configuração, prompt e esquema completos estão no [manifesto preservado](evidence/gemini-development-20/manifest.json).

## Resultados por campo
20 documentos avaliados; estados: {'ok': 20, 'empty': 0, 'error': 0}. Estado `ok` indica conclusão técnica, não acerto dos campos. Correspondência exata após normalização monetária explícita, sem tolerância. Documento com falha permanece no denominador dos campos anotados.

| Campo | Referências válidas | OCR corretos | Gemini corretos | Gemini valor incorreto | Gemini sem resposta |
|---|---:|---:|---:|---:|---:|
| total | 19 | 14 | 19 | 0 | 0 |
| subtotal | 14 | 9 | 14 | 0 | 0 |
| tax | 11 | 7 | 11 | 0 | 0 |
| service | 1 | 1 | 1 | 0 | 0 |
| discount | 0 | 0 | 0 | 0 | 0 |

Não há escore geral de acurácia. Campos sem anotação não são negativos; serviço tem apenas uma referência válida e desconto não tem referência válida. Métricas de itens ainda não foram implementadas. [Resultados completos e valores por documento](gemini-development-20.json) e [comparação gerada pelo avaliador](ocr-vs-gemini-development-20.json).

## Tempo e uso
Gemini: p50 8.333 s; p95 22.524 s. OCR: p50 1.043 s; p95 1.673 s. Percentis pelo método nearest rank. Gemini inclui pré-contagem remota de tokens, inferência e validação; OCR executa localmente em CPU. As medições por documento excluem a pausa de 15 segundos entre documentos e a gravação da saída. Não representam latência em hospedagem gratuita.

Uso informado pelo provedor em 20 respostas: 26,332 tokens de entrada e 3,689 tokens de saída normalizados (total menos entrada, incluindo pensamento quando houver). Uso por resposta permanece na evidência original. A pré-contagem é separada do uso efetivo. Custo estimado conhecido: USD 0, com taxas zero e projeto Free Tier confirmado pelo usuário, sem faturamento ativado. Isso não é fatura nem verificação do plano pela API. Limites do plano gratuito continuam sujeitos à conta. Computação e hospedagem não foram precificadas.

## Erros e abstenções observados
Não houve divergência nem abstenção nos campos com referência válida deste lote. Isso não comprova que todos os itens ou campos não anotados estejam corretos.

No documento `cord-train-shard0-row0173`, Gemini extraiu desconto `-38,500`, mas o campo não está anotado no gabarito. Uma inspeção visual pontual nesta etapa confirmou o valor impresso ao lado de 10%. O caso permanece `unannotated_prediction`, fora das métricas; o gabarito oficial não foi alterado. Não houve revisão visual integral dos 20 documentos nesta etapa.

## Cobertura das verificações aritméticas
As 76 verificações locais retornaram `skipped`, por ausência de componentes exigidos ou itens não certificados como completos. Nenhuma relação aritmética foi efetivamente aprovada neste lote. Isso é uma limitação de cobertura das regras atuais, mesmo com os acertos nos campos anotados; ausência de alerta não certifica consistência do recibo. A próxima etapa de revisão humana deve tornar esse estado visível.

## Totais recuperados em relação ao OCR
- `cord-train-shard0-row0006`: total `61,799` correto; OCR apresentou `62,000` (wrong_value).
- `cord-train-shard0-row0057`: total `39,000` correto; OCR apresentou `None` (missed).
- `cord-train-shard0-row0059`: total `25,000` correto; OCR apresentou `22,727` (wrong_value).
- `cord-train-shard0-row0062`: total `3.600.000` correto; OCR apresentou `None` (missed).
- `cord-train-shard0-row0173`: total `346,500` correto; OCR apresentou `None` (missed).

## Evidências e reprodução
Os arquivos de extração e manifestos originais foram copiados sem alteração para [evidência Gemini](evidence/gemini-development-20/manifest.json) e [evidência OCR](evidence/ocr-baseline/manifest.json). Incluem saída original, validação, tempos, configuração disponível, hashes de imagem/código/lock e commit observado. A árvore estava com alterações locais; o commit sozinho não identifica todo o código executado. Os hashes de fonte registram essa diferença. Nenhuma chave foi publicada. Imagens e gabaritos permanecem fora do Git.

As evidências publicadas de ambas as abordagens foram reavaliadas contra a amostra local verificada, sem chamar a API. O relatório Gemini foi reproduzido byte a byte. No OCR, métricas, valores por documento, hashes de origem e tempos foram reproduzidos sem diferença; apenas os textos descritivos de latência e limitações diferem porque o avaliador foi atualizado desde o relatório original. O relatório histórico foi preservado.

```powershell
uv sync --locked --extra gemini
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
uv run receipttrace evaluate-extraction --sample data/processed/cord-inspection --run docs/reports/evidence/gemini-development-20 --output runs/gemini-replay.json
uv run receipttrace evaluate-extraction --sample data/processed/cord-inspection --run docs/reports/evidence/ocr-baseline --output runs/ocr-replay.json
uv run receipttrace compare-extractions --baseline runs/ocr-replay.json --candidate runs/gemini-replay.json --output runs/comparison-replay.json
```

Use saídas novas. Se a amostra já existir, apenas verifique-a. Uma nova aquisição preserva IDs e hashes dos arquivos, mas altera a data do manifesto e seu hash; isso não altera as métricas. O [manifesto publicado da amostra original](cord-inspection.manifest.json) permite conferir a proveniência desta execução. Reavaliação dos arquivos salvos é determinística sob o mesmo avaliador; nova inferência remota pode produzir resultados diferentes. Para nova inferência, siga o [guia Gemini](../gemini.md), usando outra pasta de saída.

## Limitações e atribuição
Amostra pequena de treino, já usada no desenvolvimento; não é teste reservado. O provedor pode ter tido exposição ao CORD durante treinamento. Não comprova generalização, documentos fiscais brasileiros, conferência nota versus pedido ou qualidade de todos os itens. Anotações incompletas não são corrigidas para melhorar o resultado. Valores extraídos em campos não anotados exigem inspeção humana; não são automaticamente alucinações.

Fonte: [CORD, autores originais](https://github.com/clovaai/cord), [CORD v2 público](https://huggingface.co/datasets/naver-clova-ix/cord-v2), revisão `7f0115a4b758a71d6473b8d085751692da2fef98`, CC BY 4.0. As saídas publicadas são derivadas desses recibos; não incluem imagens. A licença dos dados é independente da licença do código.

## Verificações desta etapa
113 testes aprovados; Ruff e mypy aprovados. Integridade dos 20 documentos verificada, avaliação independente e comparação concluídas, reprodução das evidências publicadas conferida. Assistência de IA usada na execução e documentação, sujeita à revisão do responsável pelo projeto. Sem CI remota, commit, push ou deploy nesta etapa.
