# Etapas de implementação

O desenvolvimento avança por entregas que possam ser revisadas e demonstradas. A situação abaixo descreve o estágio atual; as mensagens de commit são sugestões para mudanças reais, não uma lista de commits já feitos.

| Etapa | Resultado esperado | Situação |
|---|---|---|
| Fundação | Problema, escopo, arquitetura e avaliação definidos | Documentados |
| Dados | Amostra pública com origem e integridade verificáveis | Implementada |
| Domínio | Campos, números e regras de validação testados | Implementada |
| OCR | Referência local para comparar qualidade e tempo | Executada em 20 documentos |
| IA | Integração com resposta estruturada e tratamento de falhas | Gemini executado em 20 documentos |
| Avaliação | Resultados por campo e evidências reproduzíveis | Publicados para a amostra de desenvolvimento |
| Revisão | Corrigir campos preservando o original e o motivo da mudança | Implementada localmente e testada |
| API e interface | Demonstrar exemplos e revisão em PT-BR e inglês | Implementada e verificada localmente |
| Empacotamento | Execução, Docker e integração contínua verificados | Ambiente e workflow existentes; Docker e validação remota pendentes |
| Apresentação | Estudo de caso e demonstração pública | README e demonstração local bilíngues; hospedagem pendente |

## Revisão entregue e próxima etapa

O [fluxo local de revisão](review.md) preserva a origem, registra alterações com responsável e motivo, exige versão esperada e separa revisão de verificação aritmética. Corrigir após a conclusão reabre a revisão. A verificação está documentada no [relatório da etapa](reports/review-verification.md).

O fluxo já está disponível na [aplicação web e API](web.md), com imagem, valores e histórico. A próxima etapa é preparar a hospedagem da demonstração em modo somente leitura e verificar seu comportamento no ambiente de destino. A avaliação com pessoas e em dados reservados continua pendente.

## Orientação para a apresentação

A interface deve seguir o [roteiro de apresentação](presentation.md), com conteúdo apoiado nas [perguntas de negócio](business-case.md). A demonstração inicial proposta usa exemplos já processados: problema → exemplo real → resultados → evidências → limites. A primeira interface segue essa sequência e está disponível localmente.

## Como organizar os commits

Use uma mudança coerente por commit. Exemplos de mensagens para as próximas entregas:

- `feat: add auditable receipt review workflow`
- `feat: expose receipt processing and review interface`
- `chore: add container and verify deployment workflow`
- `docs: publish project case study and demo guide`

Divida uma entrega quando houver alterações independentes, preservando o histórico real do desenvolvimento. Custos e hospedagem devem ser definidos antes das operações que dependem deles.
