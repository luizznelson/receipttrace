# Entregas revisáveis

Cada linha é uma unidade sugerida de trabalho, não um commit já realizado.

| Etapa | Evidência de conclusão | Mensagem sugerida |
|---|---|---|
| Fundação | Escopo, arquitetura e avaliação revisados | docs: define project scope and evaluation protocol |
| Dados | Amostra real inspecionada, manifesto e aquisição reproduzível | feat: add versioned CORD data ingestion |
| Domínio | Campos e regras monetárias com testes | feat: add receipt schema and validation rules |
| Referência | OCR/regras executado e limitações medidas | feat: implement OCR extraction baseline |
| IA | Adaptador, validação de saída e falhas verificadas | feat: add structured AI receipt extraction |
| Avaliação | Comparação reproduzível com resultados por documento | feat: add reproducible extraction evaluation |
| Revisão | Resultado original e alterações preservados | feat: add auditable receipt review workflow |
| API e interface | Fluxo funcional, PT-BR/EN e testes de integração | feat: expose receipt processing and review interface |
| Empacotamento | Execução documentada, Docker e CI verificados | chore: add container and continuous integration |
| Portfólio | README bilíngue, resultados e demonstração | docs: publish project case study and demo guide |

Desdobrar etapas grandes quando surgirem mudanças independentes. A primeira implementação será somente aquisição e inspeção de dados. Chaves, custos e hospedagem serão definidos antes de operações dependentes.
