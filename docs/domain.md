# Campos, números e verificações aritméticas

## Para que serve esta validação

Uma extração pode produzir um JSON válido e ainda conter números incorretos. O domínio define como representar os campos e quais relações aritméticas podem ser verificadas. Ele preserva o valor original para que uma pessoa consiga conferir sua interpretação.

As verificações são conservadoras: se um componente estiver ausente, o cálculo não é aprovado por suposição. No [lote real de 20 recibos](reports/gemini-development-20.md), as 76 verificações foram puladas. Isso limita a cobertura aritmética, mesmo com os acertos medidos na extração dos campos.

## Contrato de entrada

`RawReceipt` e `RawItem` usam Pydantic com tipos estritos e proíbem campos desconhecidos. Números extraídos são textos ou `null`; valores `float` não são aceitos. `document_id` é obrigatório. A moeda é informativa e não é deduzida da política numérica. Os gabaritos do CORD não são entrada da validação.

Cada valor normalizado mantém `raw` (texto original), `value` (valor interpretado), `status` e motivo da falha. Os estados são `missing`, `invalid` e `parsed`. Valores `Decimal` são serializados como texto no JSON. Um campo ausente continua ausente. Subitens são preservados recursivamente, sem somá-los novamente ao valor do item pai.

## Como interpretar os números

| Política | Comportamento |
|---|---|
| `idr-grouped` | Inteiros com agrupamentos de três dígitos separados por vírgula ou ponto; aceita prefixo Rp. Rejeita separadores misturados, frações e marcadores @. |
| `decimal-dot` | Ponto decimal, sem agrupamento de milhares, até quatro casas decimais. |
| `decimal-comma` | Vírgula decimal, sem agrupamento de milhares, até quatro casas decimais. |
| Quantidade | Ponto decimal e marcador x opcional antes ou depois; valor positivo. Textos agregados como `1.00xITEMS` não são tratados como quantidade de um item. |

Por exemplo, `1.234` significa mil duzentos e trinta e quatro em `idr-grouped`, mas um inteiro e 234 milésimos em `decimal-dot`. A política é obrigatória no comando; não há detecção automática.

Limites de comprimento e dígitos impedem entradas fora do contrato. Esses casos retornam `invalid`, sem aproximação. Não há arredondamento implícito. O cálculo usa um contexto de precisão próprio, separado do contexto `Decimal` de quem chama a função.

## Regras implementadas

1. **Item simples:** quantidade × preço unitário − magnitude do desconto = `amount`. Todos os componentes são necessários, inclusive desconto explicitamente zero. Itens com filhos não são avaliados por esta regra porque sua composição ainda não foi definida.
2. **Subtotal:** soma dos valores `amount` dos itens de primeiro nível. Exige lista não vazia declarada completa, valores válidos, subtotal válido e ausência de itens compostos.
3. **Total:** subtotal − magnitude do desconto + imposto + serviço. Todos os componentes devem estar explícitos. Campo ausente não significa zero.

Descontos positivos e negativos são tratados como dedução pela magnitude. `amount` representa o valor líquido da linha antes dos encargos do recibo. Um novo adaptador precisa justificar esse mapeamento para evitar aplicar o mesmo desconto duas vezes. Outros modelos de impostos e ajustes ainda não são cobertos.

## Como ler o resultado

| Estado | Significado |
|---|---|
| `pass` | A relação aritmética pôde ser verificada e os valores coincidiram. |
| `mismatch` | A relação foi verificada e apresentou diferença. |
| `skipped` | Não havia informação ou condição suficiente para verificar. |
| `invalid` | Algum valor necessário era inválido. |

As comparações registram esperado, observado e diferença (observado − esperado). A tolerância padrão é zero; o valor escolhido fica no relatório. Ausência de divergência não certifica correção: é necessário observar também as verificações puladas.

## Executar um exemplo

```powershell
uv sync --locked
uv run receipttrace validate-receipt examples/synthetic-receipt.json --policy idr-grouped
```

O exemplo é sintético e demonstra as regras; não mede qualidade de extração. O comando imprime JSON com hash SHA-256 da entrada, versões, política, tolerância, valores originais e verificações. O arquivo de entrada não é alterado.

Códigos de saída: `0` sem achados numéricos, `2` com `invalid` ou `mismatch`, `1` para erro de contrato, arquivo ou configuração. Código `0` pode conter `skipped`; esse estado é explícito no relatório.

[Contrato JSON Schema](contracts/raw-receipt.schema.json) · [Verificação histórica do domínio](reports/domain-verification.md)
