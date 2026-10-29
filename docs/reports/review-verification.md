# Verificação do fluxo de revisão — 29/10/2026

## Resultado da entrega

A revisão local foi implementada com preservação da extração original e histórico de alterações. Cada correção registra responsável declarado, motivo, momento UTC e valores antes/depois. A conclusão é uma ação explícita; uma nova correção reabre a revisão.

O fluxo usa SQLite local e comandos com pedidos em arquivos JSON. Não requer uma nova chamada de IA. API, interface e medição de trabalho humano continuam pendentes.

## Demonstração em uma extração pública

Foi usada a saída OCR de `cord-train-shard0-row0006`, já publicada na comparação. O valor original do total era `62,000`. A demonstração registrou uma correção para `61,799`, valor já documentado no estudo de caso.

O teste criou a revisão na versão 0, salvou a correção na versão 1, recusou uma nova alteração baseada na versão antiga e registrou a conclusão na versão 2. O banco foi reaberto e o estado foi reconstruído a partir dos eventos. Todos os arquivos da origem permaneceram idênticos.

O resultado separa `extraction_status=ok`, `review_status=completed` e `arithmetic.status=not_checked`. A conclusão não mudou as verificações puladas para aprovadas.

**Esta foi uma demonstração automatizada do mecanismo, não uma revisão feita por uma pessoa.** O responsável foi identificado como `automated-workflow-demo` e o motivo registra essa condição. Não houve medição de ganho de produtividade, aprovação financeira ou alteração dos resultados originais de OCR/Gemini.

[Estado final e histórico da demonstração](review-workflow-example.json) · [Manifesto da extração de origem](evidence/ocr-baseline/manifest.json)

## Verificações executadas

- 151 testes locais aprovados, incluindo 38 novos casos de revisão e comandos.
- Ruff: análise e verificação de formatação aprovadas.
- mypy: 14 módulos de origem verificados, sem erros.
- Fluxo pelos quatro comandos, persistência após reabertura e conclusão sem correção testados.
- Alteração de itens e subitens, listas completas, campos inválidos e pedidos sem mudança testados.
- Rejeição de versão antiga e duas correções simultâneas testadas; só uma gravação foi aceita.
- Falha de uma mudança em um pedido com vários campos não gravou as demais.
- Hashes, bloqueio de sobrescrita e detecção de alterações no snapshot e nos eventos testados.
- Extrações com erro ou vazias não puderam ser declaradas revisadas.
- Verificações aprovadas não concluíram a revisão automaticamente; verificações puladas e achados exigiram reconhecimento explícito.

Os testes usam exemplos sintéticos identificados e não acessam a rede. A demonstração adicional usa uma saída real já salva, sem chave de API.

## Limites conhecidos

O responsável é informado por quem registra a ação; não há autenticação nem prova de identidade. Triggers e hashes ajudam a preservar evidência e detectar inconsistências, mas não protegem contra uma pessoa com controle do banco capaz de reescrever todo o histórico. Não há assinatura digital nem ancoragem externa de hashes.

A validação usa as regras atuais da versão 1. Evolução das regras e migração de bancos precisam de tratamento de compatibilidade. O registro de uma revisão com ciência de limitações não torna o recibo apto a pagamento ou conformidade fiscal.

Não houve CI remota, inferência de IA, commit, push ou deploy nesta etapa. O banco da demonstração fica em `runs/`, fora do Git. Veja o [guia de revisão](../review.md) para executar o fluxo e os [contratos](../contracts/review-correction.schema.json) dos pedidos.
