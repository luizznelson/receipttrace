# ADR-001 — separar extração, validação e avaliação

## Decisão e motivo

O projeto começa com comandos Python executados localmente. A extração e a avaliação vêm antes da API e da interface, para verificar a qualidade da solução antes de ampliar a aplicação.

Separar essas responsabilidades permite comparar OCR e IA nos mesmos documentos, revisar as regras de negócio de forma independente e reaproveitar a lógica quando a interface for implementada. O fluxo local de extração, avaliação e revisão já está implementado, com API e interface bilíngue para os exemplos salvos e para o teste temporário de novas imagens com OCR local.

## Responsabilidades

| Área | Responsabilidade | Implementação atual |
|---|---|---|
| Dados | Obter o CORD, selecionar documentos e verificar integridade | `data.py` |
| Domínio | Representar os campos, interpretar números e verificar relações aritméticas | `domain.py`, `money.py` |
| OCR | Reconhecer texto e aplicar regras de extração | `ocr.py`, `ocr_rules.py` |
| IA | Preparar solicitações, aplicar limites e preservar respostas | `llm.py`, `llm_config.py`, `gemini.py` |
| Credenciais | Ler a chave local sem incluí-la nos resultados | `credentials.py` |
| Avaliação | Comparar resultados salvos com as anotações oficiais | `evaluation.py` |
| Revisão | Preservar a extração e registrar correções e conclusão em SQLite | `review.py` |
| Teste temporário | OCR de imagens novas, sem persistência, com limites de processamento | `uploads.py`, `upload_worker.py`, `upload_rules.py` |
| Aplicação web | Servir exemplos, indicadores e ações da revisão na mesma origem | `web.py`, `demo_catalog.py`, `static/` |
| Entrada de comandos | Receber parâmetros e coordenar a execução | `cli.py` |

O adaptador OpenAI permanece opcional e não possui avaliação real publicada. O caminho de IA medido usa Gemini. As extrações continuam em arquivos JSON. A revisão usa SQLite, com snapshot da origem, eventos de acréscimo e controle de versão em transações. O [guia de revisão](review.md) descreve os limites de auditoria e identidade.

## Separação dos dados de referência

O extrator recebe apenas imagens e parâmetros autorizados. As anotações oficiais ficam em uma pasta separada e são lidas pelo avaliador depois da extração. Elas não entram no prompt.

A saída de um modelo pode estar no formato correto e ainda conter valores errados. Por isso, Pydantic valida o contrato, as regras do domínio verificam o que for possível e o avaliador mede acertos contra a referência. São três verificações diferentes.

## Alternativas consideradas

Colocar as regras diretamente na interface simplificaria o primeiro protótipo, mas dificultaria os testes isolados e a comparação dos extratores. Distribuir o processamento em serviços separados aumentaria a operação antes de haver demanda comprovada. O fluxo local mantém a implementação pequena e permite evolução gradual.

SQLite foi escolhido para a revisão local. A interface e a API seguem a [ADR-002](architecture-web.md). A hospedagem continua pendente. Filas, microsserviços e abstrações genéricas só devem ser adicionados quando resolverem uma necessidade demonstrada.
