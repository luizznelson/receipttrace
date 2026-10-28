# Escopo inicial — proposta v0.1

## Usuário e tarefa
Uma pessoa revisora precisa transformar recibos em registros utilizáveis, verificar campos e corrigir falhas sem perder o resultado original.

## Recorte
- Entrada inicial: imagens do CORD v2, identificadas individualmente.
- Campos candidatos: descrição, quantidade, preço de item, subtotal, descontos, taxas e total. A inspeção dos dados determinará quais possuem cobertura suficiente.
- Saída: registro estruturado, alertas de validação e referência à origem.
- Revisão: registrar antes/depois, momento e motivo, preservando a extração original.

## Fora da primeira versão
NF-e brasileira, XML fiscal, conciliação com pedidos reais, pagamento, agentes autônomos, treinamento de modelos e processamento irrestrito de uploads públicos.

## Critérios de aceite finais
1. Documentos aceitos possuem resultado ou erro explícito; falhas não desaparecem do relatório.
2. Valores monetários usam Decimal e regras explícitas de separadores e arredondamento, nunca float para comparação financeira.
3. Campo ausente permanece ausente; o sistema não inventa quantidade, moeda ou preço unitário.
4. Cada resultado referencia arquivo, hash, configuração e versão do extrator.
5. Correção humana não altera o resultado original nem o gabarito de avaliação.
6. Avaliação reproduzível inclui denominadores, exclusões e exemplos de falha.
7. Uma pessoa consegue executar a demonstração a partir da documentação.
8. Interface e estudo de caso terão PT-BR e inglês; os dados originais não serão traduzidos para calcular métricas.

Não há meta numérica de acurácia definida antes da primeira referência medida. Metas serão registradas antes da avaliação final.
