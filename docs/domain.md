# Contrato dos recibos e validação — versão 1

## Entrada
`RawReceipt` e `RawItem` usam Pydantic com tipos estritos e campos desconhecidos proibidos. Valores extraídos são textos ou null, nunca float. `document_id` é obrigatório. A moeda é informativa e não é inferida da política numérica. Os gabaritos do CORD não são entrada deste comando.

Cada campo numérico normalizado preserva `raw`, `value`, `status` (missing, invalid, parsed) e motivo de falha. Decimal é serializado como texto no JSON. Nenhum campo ausente é preenchido automaticamente. Subitens são preservados recursivamente, sem somá-los novamente ao preço do pai.

## Políticas explícitas
- `idr-grouped`: valores inteiros, agrupamentos de três dígitos com vírgula OU ponto; aceita prefixo Rp. Não aceita mistura dos separadores, frações ou marcadores @.
- `decimal-dot`: ponto decimal, sem agrupamento de milhares, até quatro casas decimais.
- `decimal-comma`: vírgula decimal, sem agrupamento de milhares, até quatro casas decimais.
- Quantidade: ponto decimal, opcional x antes/depois; deve ser positiva. Contagens agregadas como `1.00xITEMS` não são presumidas como quantidade do item.

`1.234` significa 1234 na política de agrupamento, e 1,234 na política decimal-dot. A escolha é obrigatória no comando, sem detecção automática. Há limites de comprimento e dígitos; valores fora do contrato geram invalid, não aproximação. Não há arredondamento implícito. A precisão de cálculo é isolada do contexto Decimal do chamador.

## Regras conservadoras
1. Item simples: quantidade × preço unitário − magnitude do desconto = amount. Todos os componentes, inclusive desconto explicitamente zero, são necessários. Itens com filhos têm essa regra ignorada por semântica ainda indefinida.
2. Subtotal: soma dos amounts dos itens de primeiro nível. Requer lista não vazia declarada completa, amounts válidos, subtotal válido e ausência de itens compostos.
3. Total: subtotal − magnitude do desconto + taxa + serviço. Todos os componentes devem estar explícitos; campo ausente não significa zero.

Descontos positivos e negativos representam deduções pela magnitude. Amount representa o valor líquido da linha antes dos encargos de recibo; descontos no nível do recibo são aplicados separadamente. Um adaptador futuro precisa justificar esse mapeamento para não aplicar o mesmo desconto duas vezes. Outros modelos de impostos e ajustes não são cobertos.

Cada regra retorna pass, mismatch, skipped ou invalid. Comparações incluem esperado, observado e diferença (observado − esperado). Tolerância padrão: zero; a escolhida fica no relatório. Ausência de divergências não comprova correção: consultar também as verificações ignoradas.

## Uso local
```powershell
uv sync --locked
uv run receipttrace validate-receipt examples/synthetic-receipt.json --policy idr-grouped
```
Saída JSON no terminal, com hash SHA-256 da entrada, versões do esquema/regras, política, tolerância, valores originais e resultados. Não modifica o arquivo de entrada. Códigos de saída: 0 sem achados numéricos, 2 com invalid/mismatch, 1 para erro de contrato/arquivo/configuração. Código 0 pode conter skipped; isso é explícito no relatório.

O exemplo é sintético e apenas demonstra regras. Nenhuma extração de imagem ou avaliação de IA foi executada nesta etapa.

## Evidências

[Contrato JSON Schema](contracts/raw-receipt.schema.json) e [verificação desta etapa](reports/domain-verification.md).
