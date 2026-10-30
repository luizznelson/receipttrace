# Escopo e critérios de entrega

## Quem o projeto pretende ajudar

Uma pessoa responsável por conferir recibos precisa transformar imagens em registros, identificar campos duvidosos e corrigir erros sem perder o resultado original. O objetivo do ReceiptTrace é apoiar esse processo e permitir que cada decisão seja conferida depois.

A primeira versão usa recibos públicos do CORD v2. Isso permite avaliar a extração com respostas de referência conhecidas, sem depender de documentos privados de uma empresa.

## Perguntas que orientam a entrega

A primeira versão deve permitir discutir se a IA extrai melhor que o OCR, quanto tempo leva, qual foi o uso conhecido da API e como conferir cada resultado. Economia de trabalho humano e uso em novos documentos exigem avaliações posteriores. O [caso de negócio](business-case.md) relaciona cada pergunta à evidência disponível.

## O que faz parte da primeira versão

| Etapa | Entrega | Situação atual |
|---|---|---|
| Dados | Imagens identificadas, origem documentada e integridade verificável | Implementada |
| Extração | OCR e IA geram campos estruturados a partir das imagens | Implementada e avaliada em amostra de desenvolvimento |
| Validação | Formato dos campos e regras monetárias explícitas | Implementada; cobertura aritmética limitada nos dados reais |
| Avaliação | Comparação por campo, tempo, falhas e uso da API | Implementada para cinco campos de totais |
| Revisão | Correções com valor anterior, novo valor, momento e motivo | Implementada por comandos e interface para cinco campos de totais |
| Apresentação | API, interface PT-BR/EN e download da revisão em JSON | Implementada para exemplos salvos e envio temporário de PNG/JPG; hospedagem pendente |

Os campos previstos incluem descrição, quantidade, preço do item, subtotal, desconto, imposto, serviço e total. A avaliação atual mede somente os cinco campos de totais; itens ainda não têm métrica de qualidade. [Resultados e limites](reports/gemini-development-20.md).

O [fluxo de revisão](review.md) preserva a extração original em SQLite e reabre a revisão quando há nova correção. A conclusão exige ciência explícita de verificações puladas ou com achados. Não equivale a aprovação financeira.

## O que fica fora desta versão

NF-e brasileira, XML fiscal, conciliação com pedidos reais, pagamentos, agentes autônomos, treinamento de modelos e uploads públicos sem restrição não fazem parte da primeira entrega.

## Como avaliar a entrega final

1. Cada documento aceito tem um resultado ou erro explícito. Falhas permanecem no relatório.
2. Valores monetários usam `Decimal` e políticas explícitas de separadores e tolerância; comparações financeiras não usam `float`.
3. Campos ausentes continuam ausentes. A extração não deve completar quantidade, moeda ou preço por suposição.
4. Cada resultado identifica a imagem, o hash, a configuração e a versão do extrator.
5. A revisão humana preserva a extração original e não altera o gabarito usado na avaliação.
6. A avaliação informa documentos elegíveis, acertos, erros, campos sem resposta e exemplos verificáveis.
7. Outra pessoa consegue executar a demonstração seguindo a documentação.
8. A interface e o estudo de caso terão PT-BR e inglês. Os dados originais não serão traduzidos para calcular métricas.
9. A apresentação explica problema, público, perguntas de negócio, resultados e limites antes dos detalhes técnicos. Os indicadores têm evidência e o estado de revisão não é confundido com extração concluída. Veja o [roteiro da interface](presentation.md).

Ainda não foi definida uma meta de qualidade para a avaliação final. Essa meta deve ser registrada antes de usar o conjunto de teste reservado. O resultado atual é uma referência de desenvolvimento, não uma aprovação para operação financeira.
