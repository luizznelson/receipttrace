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
| Revisão | Corrigir campos preservando o original e o motivo da mudança | Pendente |
| API e interface | Demonstrar o processamento e a revisão em PT-BR e inglês | Pendente |
| Empacotamento | Execução, Docker e integração contínua verificados | Ambiente e workflow existentes; Docker e validação remota pendentes |
| Apresentação | Estudo de caso e demonstração pública | README bilíngue atualizado; demonstração pendente |

## Próxima entrega: revisão humana

A revisão deve mostrar a imagem, os valores extraídos e os limites da validação. Uma correção precisa registrar o valor anterior, o novo valor, o momento e o motivo, sem alterar a extração original. Verificação aritmética pulada deve ser apresentada como “não verificada”, sem sugerir aprovação.

Depois desse fluxo, a API e a interface poderão expor uma demonstração completa. A avaliação em dados reservados ainda precisa de planejamento e execução antes de qualquer alegação de generalização.

## Orientação para a apresentação

A interface deve seguir o [roteiro de apresentação](presentation.md), com conteúdo apoiado nas [perguntas de negócio](business-case.md). A demonstração inicial proposta usa exemplos já processados: problema → exemplo real → resultados → evidências → limites. A construção do frontend continua pendente.

## Como organizar os commits

Use uma mudança coerente por commit. Exemplos de mensagens para as próximas entregas:

- `feat: add auditable receipt review workflow`
- `feat: expose receipt processing and review interface`
- `chore: add container and verify deployment workflow`
- `docs: publish project case study and demo guide`

Divida uma entrega quando houver alterações independentes, preservando o histórico real do desenvolvimento. Custos e hospedagem devem ser definidos antes das operações que dependem deles.
