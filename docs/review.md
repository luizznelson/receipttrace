# Revisão de recibos com histórico de alterações

## Qual problema esta etapa resolve

Uma correção não deve apagar o que foi extraído. A revisão local permite conferir os campos e registrar alterações com responsável, motivo, data e valor anterior. Também registra a conclusão explícita da revisão, mesmo quando nenhuma correção é necessária.

O fluxo está implementado por comandos e banco SQLite local. A [aplicação web](web.md) também permite revisar os cinco campos de totais pela interface e expõe o mesmo domínio por API. A implementação não comprova redução de trabalho humano; isso precisa de uma avaliação própria.

## Três estados que não devem ser confundidos

| Informação | Exemplos | O que significa |
|---|---|---|
| Processamento (`extraction_status`) | `ok`, `empty`, `error` | A extração original terminou, ficou sem texto ou falhou. Esse estado não muda quando alguém corrige um valor. |
| Verificações (`arithmetic.status`) | `passed`, `partial`, `not_checked`, `findings`, `unavailable` | As regras puderam ser aplicadas, foram parcialmente aplicadas, ficaram sem componentes ou encontraram problemas. |
| Revisão (`review_status`) | `pending`, `completed`, `unavailable` | Houve uma conclusão explícita sobre a versão atual ou a revisão ainda está pendente. Extrações vazias ou com erro ficam indisponíveis para correção nesta versão. |

`passed` significa que todas as verificações geradas passaram. `partial` indica verificações aprovadas junto de outras puladas. `findings` indica divergência ou número inválido. `not_checked` significa que nenhuma relação foi efetivamente aprovada. Sem uma extração revisável, o estado é `unavailable`.

Uma revisão concluída não aprova pagamento, conformidade fiscal ou consistência de cálculos que não puderam ser verificados. O resultado da comparação com o gabarito continua pertencendo à avaliação; corrigir um campo não altera a métrica original.

## 1. Abrir uma revisão

Na raiz do projeto, com o ambiente instalado por `uv sync --locked`:

```powershell
uv run receipttrace review-start --run docs/reports/evidence/ocr-baseline --document-id cord-train-shard0-row0006
```

Esse exemplo usa uma extração pública já salva. Não chama uma API e não precisa de chave. O comando imprime o `review_id`, a `revision` atual, os campos e os estados. Copie o identificador para os próximos comandos.

O banco padrão é `runs/reviews.sqlite3`, fora do Git. Todos os comandos aceitam `--database` para escolher outro arquivo. Abrir novamente a mesma extração no mesmo banco recupera a revisão existente, sem reiniciar seu histórico.

O resultado e o manifesto originais são copiados para o banco com seus hashes. Isso mantém o histórico consultável mesmo se a pasta da execução for movida. Não são copiados a imagem nem o gabarito; mantenha a amostra para conferir a imagem.

## 2. Preparar uma correção por arquivo

Copie o exemplo para um arquivo de trabalho:

```powershell
Copy-Item examples/review-correction.example.json runs/review-correction.json
```

Edite `actor`, `reason` e os valores antes de enviar. `actor` identifica quem está registrando a ação; `reason` explica o que foi conferido. Ambos são obrigatórios e não podem conter só espaços. A identidade é declarada localmente, sem autenticação.

```json
{
  "actor": "sua-identificacao",
  "reason": "Conferi o total impresso; o OCR havia lido o valor do pagamento.",
  "changes": [
    {"path": "/total", "value": "61,799"}
  ]
}
```

O texto numérico deve seguir a política da extração. No CORD, a política é `idr-grouped`: `61,799` representa 61799. O valor original da imagem não é convertido automaticamente para o formato brasileiro.

```powershell
uv run receipttrace review-correct --review-id SEU_REVIEW_ID --expected-revision 0 --request runs/review-correction.json
```

Use a revisão retornada pelo último comando, não necessariamente `0`. A ação é recusada se outra alteração já tiver ocorrido. Reabra com `review-show`, confira as mudanças e só então envie uma nova ação.

Cada correção salva o valor anterior e o novo valor. Uma ação pode mudar até 100 campos, sem caminhos duplicados ou sobrepostos. Se qualquer mudança for inválida, nenhuma delas é gravada.

### Quais campos podem ser alterados

Os caminhos usam JSON Pointer, por exemplo:

| Caminho | Alteração |
|---|---|
| `/total`, `/subtotal`, `/tax`, `/service`, `/discount`, `/currency` | Campo do recibo; texto ou `null`. |
| `/items/0/amount` | Valor do primeiro item existente. |
| `/items/0/children/0/description` | Descrição do primeiro subitem existente. |
| `/items` ou `/items/0/children` | Substituição da lista inteira, inclusive para adicionar ou remover itens. |
| `/items_complete` | Declaração booleana sobre a completude da lista, com motivo registrado. |

Também é possível substituir um item existente inteiro. Índices começam em zero. Não é permitido alterar `document_id`, metadados, política numérica ou tolerância. A lista final precisa respeitar `RawReceipt` e `RawItem`. Alterar um texto monetário para outro formato inválido pode ser registrado como rascunho, mas aparece como `findings`; o contrato não transforma essa entrada em número correto.

Se o campo já tem exatamente o valor enviado, o sistema recusa a correção sem mudança. Para registrar que uma versão foi conferida sem edição, use a conclusão da revisão.

## 3. Concluir a revisão explicitamente

Copie o segundo exemplo e edite responsável e motivo:

```powershell
Copy-Item examples/review-completion.example.json runs/review-completion.json
```

O arquivo tem dois reconhecimentos, ambos `false` por padrão:

- `acknowledge_unverified`: precisa ser `true` se houver verificações puladas. Confirma ciência da falta de verificação; não aprova o cálculo.
- `acknowledge_findings`: precisa ser `true` se houver divergências ou números inválidos. O motivo deve explicar a situação; o alerta permanece visível.

Não marque os campos automaticamente. Leia as verificações e registre no motivo o que foi efetivamente conferido e o que continua sem confirmação.

```powershell
uv run receipttrace review-complete --review-id SEU_REVIEW_ID --expected-revision 1 --request runs/review-completion.json
```

Use a revisão atual. A conclusão gera um evento mesmo sem alteração de valores. Concluir a mesma versão novamente é recusado. Se houver uma correção posterior, o estado volta para `pending` e é necessária uma nova conclusão.

## 4. Consultar campos, estados e histórico

```powershell
uv run receipttrace review-show --review-id SEU_REVIEW_ID
```

O JSON apresenta `original_raw`, `current_raw`, verificações recalculadas, eventos e origem. O histórico informa sequência, data UTC, responsável, motivo e alterações antes/depois. A consulta verifica os hashes e reaplica os eventos para reconstruir o estado; não confia em um valor final sobrescrito.

## Decisões técnicas e limites de auditoria

SQLite é da biblioteca padrão do Python e não requer serviço externo. Cada gravação usa uma transação `BEGIN IMMEDIATE` e confere a revisão esperada dentro dela. Dois envios concorrentes baseados na mesma versão não podem ser aceitos como se fossem uma única alteração.

As tabelas preservam um snapshot da extração e eventos somente de acréscimo. Triggers recusam `UPDATE` e `DELETE`; hashes relacionam snapshot e sequência dos eventos. Essas medidas detectam alterações acidentais e inconsistências. Não são assinatura digital nem proteção contra alguém que controle o arquivo do banco e possa remover triggers ou reescrever todos os hashes. Não há autenticação, prova de identidade, armazenamento externo de hashes ou migração de versões implementados.

As verificações usam as regras atuais do domínio, versão 1. A origem guarda a validação original integral; a revisão recalcula o estado para os campos atuais. Evoluções dessas regras exigirão tratar a compatibilidade do histórico.

Não apague o banco se precisar do histórico. Faça cópias com a aplicação parada ou com a ferramenta de backup do SQLite. Bancos e arquivos de trabalho não entram no Git. Os comandos retornam código `0` em sucesso e `1` para erros, conflitos ou requisitos de conclusão não atendidos. Um código `0` não indica aprovação financeira.

[Contrato de correção](contracts/review-correction.schema.json) · [Contrato de conclusão](contracts/review-completion.schema.json) · [Verificação do fluxo](reports/review-verification.md)
