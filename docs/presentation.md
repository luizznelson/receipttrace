# Jornada e apresentação do produto

## Objetivo da apresentação

Uma pessoa deve entender qual problema o ReceiptTrace trata, ver um exemplo real e localizar a evidência dos resultados. A primeira leitura deve servir a quem avalia o valor do projeto; detalhes de implementação ficam disponíveis para quem precisa investigar.

Este documento orienta a apresentação e sua evolução. A primeira interface está implementada com três exemplos, PT-BR/EN e revisão de cinco campos de totais. O [guia da aplicação](web.md) descreve o uso e os limites atuais. A base de conteúdo é o [caso de negócio](business-case.md).

## Jornada atual: da proposta ao teste

1. Entender o problema: ler o recibo não elimina a necessidade de conferir.
2. Experimentar: escolher uma imagem própria ou seguir direto para exemplos prontos.
3. Acompanhar: recebimento e OCR com estado de espera real, sem porcentagens inventadas.
4. Conferir: imagem ao lado dos valores, trechos de origem e dúvidas explícitas.
5. Levar o resultado: corrigir, registrar motivo, conferir formato/cálculos e baixar original mais versão atual.
6. Investigar o estudo: explorar três casos públicos e consultar os resultados dos 20 documentos.

O [teste de imagens próprias](uploads.md) está implementado em PT-BR e inglês. Sua contagem de campos não é apresentada como acurácia e seus resultados não modificam o estudo. O [relatório de verificação](reports/uploads-verification.md) separa testes reais no navegador de cenários sintéticos.

## Estrutura da apresentação pública

| Ordem | Seção | O que a pessoa deve entender | Conteúdo ou ação sugerida |
|---|---|---|---|
| 1 | Problema e proposta | Para que serve o projeto e quem faria a conferência | Título claro, uma frase de contexto e ação “Testar meu recibo”, com alternativa de exemplos prontos |
| 2 | Um exemplo de recibo | Como a imagem se transforma em campos conferíveis | Imagem ao lado dos valores extraídos, origem e situação das verificações |
| 3 | Perguntas e resultados | O que melhorou e o que custou mais tempo | Comparação OCR/IA, contagens e tempo de processamento |
| 4 | Como conferir | Por que o resultado pode ser investigado | Documento, resposta original e evidência da avaliação |
| 5 | Limites e estágio | O que já funciona e o que continua pendente | Amostra de desenvolvimento, itens não avaliados e edição visual limitada a cinco campos de totais |
| 6 | Implementação e reprodução | Como o trabalho foi construído e pode ser verificado | Link para repositório, documentação e relatório detalhado |

### Texto inicial proposto

**Título PT-BR:** “Da imagem do recibo aos dados que você pode conferir.”

**Apoio PT-BR:** “Compare a leitura por OCR e IA, veja de onde veio cada valor e entenda o que ainda precisa de revisão.”

**Título EN:** “From receipt images to data you can check.”

**Apoio EN:** “Compare OCR and AI extraction, trace each value to its source, and see what still needs review.”

As ações disponíveis devem corresponder a fluxos implementados: envio temporário e exportação para novos recibos; revisão persistente apenas local para exemplos. Não oferecer aprovação fiscal ou de pagamento.

## Jornada da demonstração inicial

1. A pessoa abre um exemplo público já processado, sem fornecer chave de API.
2. Vê a imagem e os campos principais na mesma tela, com comparação entre OCR e IA quando disponível.
3. Seleciona um campo para localizar seu valor original e o resultado da comparação com a referência.
4. Entende quais verificações foram executadas, quais ficaram sem informação e o que não foi avaliado.
5. Acessa o relatório do lote e os detalhes técnicos se quiser conferir o método.

A primeira demonstração pública proposta usa resultados salvos. Isso permite apresentar o trabalho sem depender de novas chamadas ou de cota disponível no momento da visita. Três imagens originais fazem parte do pacote, com atribuição do CORD e hashes conferidos. O dataset completo e os arquivos de gabarito continuam fora do Git. A chave nunca deve ir para o navegador.

## Quais números mostrar e como explicá-los

| Informação visível | Apresentação proposta | Contexto obrigatório |
|---|---|---|
| Amostra | “20 recibos avaliados” | Desenvolvimento no CORD, sem teste reservado |
| Total do recibo | “19 de 19 totais corretos com IA” | Só 19 documentos possuem referência válida para esse campo; OCR acertou 14 |
| Ganho observado | “5 totais adicionais recuperados” | Comparação dos mesmos documentos; não equivale a horas economizadas |
| Tempo típico | “8,33 s por recibo com IA” | Mediana observada; inclui pré-contagem e inferência, exclui pausas entre documentos |
| Custo de API | “US$ 0 estimados neste experimento” | Free Tier confirmado, sem faturamento; computação e hospedagem não incluídas |

O resumo não deve mostrar “100% de precisão”, “zero erros” ou “pronto para produção” sem o recorte dos campos e da amostra. Não usar um gráfico financeiro fictício nem um indicador de economia ainda não medido. Os valores precisam vir do relatório publicado, sem cópias manuais divergentes no frontend.

## Tela do documento: separar três perguntas

| Pergunta da pessoa usuária | Informação necessária | Cuidado de apresentação |
|---|---|---|
| O que foi lido? | Campo, valor extraído, método e imagem original | Preservar a escrita original; não assumir moeda pela interface |
| O valor bate com a referência? | Correto, divergente, sem resposta ou sem referência | Referência existe nos exemplos avaliados; um novo documento pode não ter gabarito |
| A conta pôde ser verificada? | Resultado de cada regra e motivo quando não executada | “Não verificada” não é “Aprovada” |

O estado técnico de processamento, o acerto em relação ao gabarito, a validação aritmética e a revisão humana devem aparecer separadamente. Uma extração concluída pode conter valor errado. Uma conta sem divergência pode não ter sido verificada.

## Vocabulário PT-BR e inglês

| Conceito | PT-BR | English |
|---|---|---|
| Processamento terminado | Extração concluída | Extraction completed |
| Falha técnica | Falha na extração | Extraction failed |
| Campo correto contra o gabarito | Confere com a referência | Matches reference |
| Campo divergente do gabarito | Diverge da referência | Differs from reference |
| Campo não extraído | Sem resposta | No extracted value |
| Campo sem gabarito | Sem referência para comparação | No reference available |
| Regra aritmética aprovada | Cálculo confere | Arithmetic matches |
| Regra aritmética divergente | Divergência no cálculo | Arithmetic mismatch |
| Regra aritmética pulada | Não verificada | Not checked |
| Número inválido para a regra | Valor inválido para verificação | Invalid value for check |
| Revisão ainda não feita | Revisão pendente | Review pending |

Esses textos são a proposta de apresentação. O estado “Revisão concluída” deve vir de um evento de conclusão persistido pelo fluxo local, nunca da ausência de alertas. A interface deve mostrar a revisão atual e reenviá-la como versão esperada ao corrigir ou concluir; em conflito, precisa solicitar nova conferência.

## Apresentação visual e acessibilidade

- Priorizar imagem, valores, explicação do resultado e ação disponível. JSON, tokens, hashes e parâmetros ficam em uma área de detalhes técnicos.
- Usar hierarquia de títulos, espaçamento consistente, tabelas curtas e números acompanhados de rótulos e contexto.
- Fazer a comparação lado a lado em telas amplas e em sequência em telas pequenas, mantendo claro qual método gerou cada valor.
- Identificar estados por texto; cor e ícone são complementos. Garantir contraste, navegação por teclado e foco visível.
- Permitir alternar PT-BR/EN sem perder o exemplo selecionado. Traduzir a interface, preservando o texto original do recibo e das evidências.
- Diferenciar valores exibidos para leitura de valores originais. Datas e números de indicadores podem seguir o idioma; valores do recibo não devem ganhar moeda ou interpretação sem suporte nos dados.
- Explicar estados vazios e falhas com a próxima ação possível, sem atribuir sucesso a um dado ausente.

## O que verificar antes de publicar

1. Uma pessoa encontra o problema e o público proposto no início da página.
2. Um exemplo real relaciona imagem, campos extraídos e resultado, sem exigir terminal.
3. Os indicadores conferem com os relatórios e apresentam o tamanho da amostra.
4. Há acesso aos limites, ao método e às evidências, sem expor a chave.
5. A interface distingue processamento, comparação com referência, regra aritmética e revisão humana.
6. Todos os botões têm uma ação implementada; não há promessa de revisão ou exportação ainda indisponível.
7. O mesmo conteúdo essencial está disponível em PT-BR e inglês, com verificação em tela pequena e por teclado.

A primeira implementação usa FastAPI e módulos JavaScript sem build, conforme a [ADR-002](architecture-web.md). O visual foi verificado em desktop e celular; hospedagem continua pendente. O objetivo destas regras é manter a apresentação fiel ao produto e aos resultados existentes.
