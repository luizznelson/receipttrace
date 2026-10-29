# Primeiro teste real — 28/10/2026

## Resultado desta etapa

As primeiras tentativas não geraram uma extração: houve indisponibilidade de modelo, uso inicial de uma chave diferente e timeouts. A investigação posterior encontrou um erro no esquema enviado e validou a integração com outro modelo. Os registros abaixo preservam a sequência do diagnóstico.

Registro histórico: descreve o que foi verificado nesta etapa. O [relatório comparativo atual](gemini-development-20.md) apresenta os resultados posteriores de OCR e Gemini.

Documento público: cord-train-shard0-row0006, mesma imagem usada na referência OCR.

- Gemini 2.5 Flash: contagem recusada com HTTP 404; o provedor informou indisponibilidade para novas contas e recomendou 3.8 Flash.
- Gemini 3.8 Flash: contagem de entrada concluída, 1.311 tokens.
- Geração: HTTP 403 PERMISSION_DENIED, Free Tier indisponível para este projeto.
- Nenhuma resposta de extração foi obtida. Não há resultado de acurácia, tokens de saída ou custo faturado para relatar.
- Nenhum faturamento foi ativado. Solicitações interrompidas após diagnóstico de elegibilidade.

Os registros das tentativas ficam em runs/gemini-first-test, fora do Git. Nenhuma chave ou identificador de projeto está publicado neste relatório. A recomendação de usar Free Tier depende de elegibilidade efetiva, que não pode ser comprovada só pela existência da chave ou pela contagem de tokens.

Naquele momento, o próximo passo considerado era verificar a elegibilidade do projeto ou outra credencial gratuita. A correção da associação da chave e a resolução posterior estão registradas abaixo.

## Correção de associação da chave e novas tentativas

A chave inicialmente usada era diferente da exibida pelo usuário no AI Studio. Portanto, o bloqueio de elegibilidade anterior não deve ser atribuído ao projeto exibido naquela imagem.

Após atualização, a correspondência foi verificada apenas pelo sufixo, sem publicar credenciais. Com a chave correta, a contagem de entrada funcionou. A geração não respondeu dentro de 60 segundos; uma segunda tentativa com 180 segundos também terminou em ReadTimeout. Nenhuma resposta de extração ou uso de saída foi recebida. Não há evidência de rejeição por Free Tier nessas duas tentativas e não há custo faturado verificado. Não foram enviados os 20 documentos. Nenhum faturamento foi ativado.

A integração Gemini agora admite espera de até 180 segundos. Os oito testes HTTP simulados passaram, assim como mypy nos 13 módulos. Naquele ponto da investigação, a execução real ainda estava inconclusiva por timeout. Não foram feitas retentativas automáticas.

## Resolução posterior

A auditoria corrigiu a complexidade do esquema remoto e adotou Flash-Lite com raciocínio mínimo na API Interactions. A extração real completa funcionou. Consulte a [auditoria da integração](gemini-api-audit.md) para evidências e limitações; os erros acima são registros históricos.
