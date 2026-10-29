# Auditoria e correção da integração Gemini — 28/10/2026

## Conclusão
Havia um erro confirmado no esquema de transporte: o contrato Pydantic enviado com limites grandes de arrays aninhados foi rejeitado pelo provedor com HTTP 400, "too many states". Os testes simulados anteriores não comprovavam aceitação pelo servidor. A integração corrigida concluiu a extração real de um recibo com o contrato completo.

## Evidências por etapa
- GenerateContent, 3.8 Flash, texto mínimo e limite de 32 tokens: HTTP 200, MAX_TOKENS, 29 tokens de pensamento, sem texto final útil, aproximadamente 34,9 s.
- Interactions, 3.8 Flash, raciocínio baixo, texto mínimo: timeout em 45 s. Imagem com esquema de cinco campos: timeout em 90 s. Portanto não se pode atribuir todos os timeouts ao esquema completo ou exclusivamente ao endpoint antigo.
- Interactions, 3.5 Flash-Lite, raciocínio mínimo, imagem com cinco campos: completed em aproximadamente 2,9 s.
- Integração completa com contrato original: HTTP 400 por gramática excessivamente complexa.
- Integração completa com esquema simplificado: status ok em aproximadamente 4,1 s; 1.312 tokens de entrada e 213 tokens de saída informados pelo provedor.

## Mudanças
- API Interactions atual, store=false, entrada multimodal e response_format documentados.
- Leitura da resposta em steps/model_output e do uso em usage, sem interpretar pensamento como resposta final.
- Modelo recomendado: Gemini 3.5 Flash-Lite com thinking_level=minimal, listado no plano gratuito na data da pesquisa. Sem upgrade de faturamento ou fallback pago.
- Limites de arrays removidos apenas do esquema remoto; contratos locais continuam limitados e testados.
- Diagnóstico específico GeminiSchemaTooComplex e impressão de estado por documento, sem corpo de erros ou segredos.
- Configuração por .env preservada. runs/gemini-config.json preparado se ainda não existia, usando confirmação de Free Tier já fornecida pelo usuário.

## Resultado do recibo
Documento: cord-train-shard0-row0006, selecionado manualmente por já ter falhado no OCR. Dois itens extraídos, subtotal 56,181, imposto 5,618 e total 61,799. Os três valores coincidem com o gabarito. Campos não impressos permanecem null; completude dos itens não foi certificada. O resultado de um documento não é estimativa de acurácia geral nem comparação estatisticamente válida.

## Verificação
113 testes locais aprovados, Ruff e mypy aprovados. Testes novos cobrem formato Interactions, controle de raciocínio, exclusão de pensamento da resposta, esquema simplificado e manutenção dos limites locais. Não houve CI remota, commit, push ou deploy. Não foi executado lote de 20 documentos.

## Referências oficiais
- [Limites de esquemas](https://ai.google.dev/gemini-api/docs/structured-output#limitations)
- [API atual e suporte ao legado](https://ai.google.dev/gemini-api/docs/interactions-overview)
- [Pensamento e limite de saída](https://ai.google.dev/gemini-api/docs/thinking#controlling-thinking)
- [Preço e plano gratuito](https://ai.google.dev/gemini-api/docs/pricing)

Resultados brutos dos diagnósticos ficam em runs/gemini-api-audit, fora do Git. Nenhuma chave está publicada.
