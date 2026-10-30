# Um recibo, duas leituras e uma decisão de engenharia

## Por que construir isto

O cenário proposto é uma equipe administrativa organizando comprovantes. Transcrever um número não basta: o documento pode ter subtotal, pagamento e troco. Uma extração concluída pode escolher o valor errado e dificultar a conferência posterior.

No documento público `cord-train-shard0-row0006`, o OCR selecionou `62,000` como total. A anotação oficial informa `61,799`; o Gemini recuperou esse valor. A imagem mostra por que retornar ao documento é importante. Os números seguem a convenção original, sem conversão para reais.

## Como a investigação virou um produto demonstrável

1. **Dados verificáveis.** Selecionar recibos públicos com versão fixada, semente e hashes, mantendo imagens separadas dos gabaritos recebidos pelo avaliador.
2. **Uma referência simples.** Executar OCR com regras explícitas antes de adotar uma solução por modelo de linguagem.
3. **Uma comparação controlada.** Processar os mesmos 20 documentos com Gemini e comparar campos, tempo e uso conhecido da API.
4. **Regras independentes do extrator.** Preservar texto, interpretar separadores explicitamente e conferir cálculos somente quando os componentes existem.
5. **Conferência rastreável.** Mostrar imagem e valores juntos; registrar alterações e motivos, preservando o original.
6. **Uma experiência acessível.** Oferecer caso guiado, exemplo pronto, imagem própria, português/inglês e downloads para planilhas ou inspeção técnica.

## O que os resultados permitem decidir

O Gemini acertou 19 de 19 totais com referência válida; o OCR acertou 14. Isso justifica continuar investigando o ganho de leitura. O OCR teve menor tempo mediano, mas os escopos de medição são diferentes. O custo estimado de API foi zero sob o Free Tier daquele experimento, sem medir custo operacional completo.

Esses resultados não eliminam a revisão. A amostra já foi usada no desenvolvimento, itens não foram avaliados e todas as 76 verificações aritméticas ficaram sem componentes suficientes. Economia de trabalho e desempenho em documentos brasileiros ainda precisam ser medidos.

## O que inspecionar na implementação

| Habilidade demonstrada | Decisão concreta | Evidência |
| --- | --- | --- |
| Avaliação de IA | Incluir falhas e campos vazios; comparar a mesma amostra. | [Protocolo](evaluation.md) e [resultados](reports/gemini-development-20.md) |
| Modelagem do domínio | Separar texto original, Decimal e política numérica. | [Regras](domain.md), `money.py`, `domain.py` e seus testes |
| Engenharia de API | Validar entradas e distinguir conflitos, indisponibilidade e erros internos. | [Contrato](contracts/web-openapi.json), `web.py`, `web_boundary.py` |
| Integridade e revisão | Usar hashes, transações e versão esperada, com limites de confiança declarados. | [Revisão](review.md), `review.py` e testes de concorrência/integridade |
| Processamento de arquivos | Verificar imagens em memória, limitar tempo e concorrência e encerrar o trabalhador. | [Uploads](uploads.md) e `test_uploads.py` |
| Comunicação de produto | Separar o teste sem gabarito do estudo medido e explicar dúvidas junto dos valores. | Interface bilíngue, [guia web](web.md) e [qualidade](quality.md) |

## Como apresentar em poucos minutos

Explique o erro de total no recibo público. Abra “Experimentar este caso”, confira a imagem e corrija o total com motivo. Baixe a tabela ou o registro completo. Mostre que isso não altera os resultados publicados. Por fim, abra a comparação do lote e uma decisão de engenharia com seu teste correspondente.

O projeto é um trabalho de portfólio com assistência de IA, não uma implantação comprovada em empresa. Compreender o código, justificar escolhas e revisar as evidências faz parte da responsabilidade do mantenedor.
