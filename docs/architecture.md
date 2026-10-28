# ADR-001 — separação de responsabilidades

Estado: proposta inicial, sujeita à inspeção dos dados.

## Decisão
Começar com um pipeline Python executável localmente. Adicionar API e interface após validar extração e avaliação. Escolher provedores e bibliotecas após um experimento pequeno e documentado.

## Responsabilidades previstas
- Dados: aquisição, manifesto, revisão e seleção de documentos.
- Domínio: representação dos campos, normalização monetária e regras de validação.
- Extração: adaptadores intercambiáveis para OCR/regras e modelo de IA.
- Aplicação: coordenação do processamento e da revisão.
- Avaliação: comparação independente com anotações esperadas.
- Persistência: resultados originais, erros e eventos de correção.
- API/interface: apresentação e entrada, sem duplicar regras do domínio.

## Limites
O extrator recebe somente imagem e parâmetros autorizados. Anotações de referência pertencem ao avaliador e não entram no prompt nem na entrada do extrator. Saídas extraídas são dados não confiáveis e passam por validação.

Não criar filas, microsserviços ou camadas genéricas sem necessidade demonstrada. Banco de dados, frontend e hospedagem ainda não estão escolhidos.

## Alternativas
Uma aplicação única com regras na interface acelera o protótipo, mas dificulta avaliação isolada. Um sistema distribuído aumenta o custo operacional cedo demais. A proposta permite testes locais e evolução incremental.
