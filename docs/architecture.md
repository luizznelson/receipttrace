# ADR-001 — separar extração, validação e avaliação

## Decisão e motivo

O projeto começa com comandos Python executados localmente. A extração e a avaliação vêm antes da API e da interface, para verificar a qualidade da solução antes de ampliar a aplicação.

Separar essas responsabilidades permite comparar OCR e IA nos mesmos documentos, revisar as regras de negócio de forma independente e reaproveitar a lógica quando a interface for implementada. O fluxo local já está implementado; API, revisão humana e interface continuam pendentes.

## Responsabilidades

| Área | Responsabilidade | Implementação atual |
|---|---|---|
| Dados | Obter o CORD, selecionar documentos e verificar integridade | `data.py` |
| Domínio | Representar os campos, interpretar números e verificar relações aritméticas | `domain.py`, `money.py` |
| OCR | Reconhecer texto e aplicar regras de extração | `ocr.py`, `ocr_rules.py` |
| IA | Preparar solicitações, aplicar limites e preservar respostas | `llm.py`, `llm_config.py`, `gemini.py` |
| Credenciais | Ler a chave local sem incluí-la nos resultados | `credentials.py` |
| Avaliação | Comparar resultados salvos com as anotações oficiais | `evaluation.py` |
| Entrada de comandos | Receber parâmetros e coordenar a execução | `cli.py` |

O adaptador OpenAI permanece opcional e não possui avaliação real publicada. O caminho de IA medido usa Gemini. Os resultados atuais são arquivos JSON; a persistência de correções humanas ainda será definida.

## Separação dos dados de referência

O extrator recebe apenas imagens e parâmetros autorizados. As anotações oficiais ficam em uma pasta separada e são lidas pelo avaliador depois da extração. Elas não entram no prompt.

A saída de um modelo pode estar no formato correto e ainda conter valores errados. Por isso, Pydantic valida o contrato, as regras do domínio verificam o que for possível e o avaliador mede acertos contra a referência. São três verificações diferentes.

## Alternativas consideradas

Colocar as regras diretamente na interface simplificaria o primeiro protótipo, mas dificultaria os testes isolados e a comparação dos extratores. Distribuir o processamento em serviços separados aumentaria a operação antes de haver demanda comprovada. O fluxo local mantém a implementação pequena e permite evolução gradual.

Banco de dados, interface e hospedagem ainda não têm implementação consolidada neste registro. Filas, microsserviços e abstrações genéricas só devem ser adicionados quando resolverem uma necessidade demonstrada.
