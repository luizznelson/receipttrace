# Referência inicial: OCR e regras — 28/10/2026

Execução real em Windows, Python 3.14.3, CPU e modelos fixados no lock. [Resultados por documento e metadados](ocr-baseline.json).

## Resultado
20 documentos processados; 20 com texto, zero falhas de inferência. Isso não significa que todos foram extraídos corretamente.

| Campo | Referências válidas | Corretos | Valores incorretos | Sem resposta |
|---|---:|---:|---:|---:|
| total | 19 | 14 | 2 | 3 |
| subtotal | 14 | 9 | 0 | 5 |
| tax | 11 | 7 | 0 | 4 |
| service | 1 | 1 | 0 | 0 |
| discount | 0 | 0 | 0 | 0 |

Total: 14/19 corretos (73,7% de recall exato); 14/16 respostas numéricas corretas (87,5% de precisão entre os campos anotados respondidos). Esses denominadores respondem perguntas diferentes. Serviço tem apenas um exemplo; desconto não tem exemplo anotado na amostra e sua métrica fica indefinida.

Latência p50: 1.043 s; p95: 1.673 s. Inicialização: 0.921 s. CPU com uma thread; primeira inferência incluída, sem cache. Não é medição de desempenho em hospedagem gratuita.

## Erros observados
- Linha 6: agrupamento geométrico associou o rótulo GRAND TOTAL ao pagamento em dinheiro; previu 62.000 em vez de 61.799.
- Linha 59: SUB.TOTAL não foi reconhecido como subtotal e acabou tratado como total; previu 22.727 em vez de 25.000.
- Linha 57: o total está rotulado DUE, ainda não suportado.
- Linha 62: a regra evita rótulos TOTAL com QTY para não confundir contagem e dinheiro; isso também causa abstenção neste layout.
- Linha 173: texto degradado e abreviação TL. não produziram candidato suportado.

Não foram adicionadas correções específicas após observar esses erros nesta execução. Servem para planejar a próxima versão, que será avaliada separadamente. Itens extraídos são candidatos incompletos e ainda não foram pontuados.

## Limites
Amostra pequena de desenvolvimento, só um arquivo de treino. Não representa resultado em teste reservado nem em notas fiscais brasileiras. Ausências de anotação não provam que o documento não possui um campo. Pesos públicos podem ter exposição prévia ao benchmark. Não houve inferência paga; custo computacional não foi estimado.

## Verificação
73 testes locais passaram, incluindo falha simulada de OCR mantida no denominador e detecção de adulteração do resultado. Ruff e mypy passaram. Execução do OCR real e avaliação foram realizadas; CI remota e deploy não foram executados. Nenhum commit foi criado nesta etapa.
