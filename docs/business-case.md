# Problema, perguntas de negócio e valor esperado

## Qual problema o projeto trata

Uma imagem de recibo não é um registro pronto para consulta ou conferência. Alguém precisa identificar os valores, transcrevê-los e resolver dúvidas: o número representa o total, o dinheiro entregue ou o troco? Um campo está ausente ou apenas ilegível?

O ReceiptTrace trata essa passagem da imagem para dados estruturados, preservando a origem do resultado. A demonstração compara duas formas de extração e prepara as informações para revisão humana. O fluxo de revisão local já está implementado; a interface permanece pendente.

## Quem se beneficiaria e em qual tarefa

O cenário de uso proposto é uma equipe administrativa ou financeira que organiza comprovantes. A pessoa revisora precisa conferir os valores antes de usá-los em outro processo. A gestão precisa entender qualidade, tempo, custo e limites antes de considerar uma automação.

Esse cenário orienta o produto; não representa uma empresa cliente nem uma implantação real. Os documentos usados são recibos públicos do CORD v2, não notas fiscais brasileiras. A aplicação não decide pagamentos nem valida conformidade fiscal.

## Antes, proposta e resultado já demonstrado

| Aspecto | Situação que se pretende melhorar | Proposta do projeto | O que já foi demonstrado |
|---|---|---|---|
| Organização | Valores disponíveis apenas em uma imagem | Extrair campos identificados e preservar o texto original | Saídas estruturadas para 20 recibos |
| Qualidade | Transcrição ou leitura pode confundir valores | Comparar OCR e IA com referências conhecidas | Gemini recuperou cinco totais que o OCR errou ou não respondeu |
| Conferência | Um resultado sem origem é difícil de investigar | Associar cada resultado ao documento e à configuração | Respostas, hashes e resultados por documento preservados |
| Correção | Alterações podem apagar o valor originalmente extraído | Registrar antes, depois, momento e motivo | Histórico implementado em SQLite; uso por pessoas ainda não medido |
| Produtividade | Digitação e conferência consomem trabalho | Apoiar a revisão com campos preenchidos | Economia de tempo humano ainda não medida |

## Perguntas de negócio e respostas disponíveis

| Pergunta | Evidência atual | Decisão ou próximo passo |
|---|---|---|
| A IA lê os valores melhor que uma solução de OCR com regras? | Nesta amostra, totais corretos: Gemini 19 de 19; OCR 14 de 19. Subtotais: 14 de 14 versus 9 de 14. Impostos: 11 de 11 versus 7 de 11. | Há evidência para continuar o experimento com IA. Avaliar dados reservados antes de generalizar. |
| Quanto tempo leva para processar um recibo? | Mediana de 8,33 s para Gemini e 1,04 s para OCR, com etapas de medição diferentes. | O OCR foi mais rápido e a IA recuperou mais campos. Tempo de revisão humana e espera total ainda precisam ser medidos. |
| Quanto custa usar a API? | Estimativa conhecida de US$ 0 no lote, sob Free Tier confirmado e sem faturamento ativado. Computação e hospedagem não foram estimadas. | O experimento coube na configuração gratuita usada. Não há custo operacional completo nem projeção validada em escala. |
| É possível confiar automaticamente nos resultados? | O formato foi validado, mas itens não foram pontuados e as 76 verificações aritméticas foram puladas. | Não há evidência para aprovação automática. Exibir campos e verificações pendentes para revisão. |
| É possível investigar um resultado depois? | Resposta original, configuração, hashes e avaliação por documento estão publicados. | A extração já pode ser auditada. O histórico de correções está implementado localmente. A identidade é declarada, sem autenticação. |
| A solução reduz trabalho manual? | Não houve comparação com pessoas nem medição de esforço operacional. | Medir tempo de digitação, conferência e correção antes e depois, no mesmo tipo de tarefa. |
| Funciona em outros recibos ou em documentos brasileiros? | Só a amostra de desenvolvimento do CORD foi avaliada. | Testar dados reservados e definir outro estudo para documentos brasileiros. |

As respostas acima devem orientar o README, a apresentação e os indicadores da interface. Toda alegação deve apontar para uma medição ou ser identificada como hipótese.

## O que medir quando houver uso da revisão por pessoas

Estas são propostas de medição, ainda sem resultados:

- Tempo por documento: transcrição manual comparada à extração seguida de conferência e correção. Incluir os mesmos passos de trabalho nas duas condições.
- Campos corrigidos: quantos valores foram alterados em relação ao total de campos efetivamente revisados.
- Documentos revisados: distinguir “aberto”, “corrigido” e “revisão concluída”. Abrir a tela não comprova revisão.
- Qualidade após revisão: conferir o resultado final contra uma referência independente, além do resultado original da extração.
- Custo completo: API, computação, hospedagem e esforço de revisão, sob condições de uso registradas.

Metas de ganho ou critérios de aprovação deverão ser definidos antes da avaliação correspondente. Não preencher a apresentação com números hipotéticos que pareçam resultados reais.

## Como contar a história do projeto

**Problema:** transformar imagens em registros exige leitura e conferência, e os erros precisam ser investigáveis.

**Escolha de engenharia:** comparar uma solução local de OCR com uma IA nas mesmas imagens, usando referências separadas da extração.

**Resultado:** a IA recuperou cinco totais adicionais nesta amostra, com maior tempo de processamento. A solução preserva evidências para conferência.

**Limite e evolução:** isso ainda não prova ganho de produtividade nem autoriza aprovação automática. A revisão local foi implementada. O próximo passo é expô-la pela aplicação e medir sua contribuição com pessoas.

[Resultados completos](reports/gemini-development-20.md) · [Escopo](scope.md) · [Roteiro da apresentação e da interface](presentation.md)
