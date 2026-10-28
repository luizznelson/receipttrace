# ReceiptTrace

Extração de recibos com avaliação rastreável e revisão humana.

[English](README.en.md)

## Estado atual
Etapa de aquisição e inspeção dos dados. Extrator, benchmark, API e interface ainda não foram implementados. Não há resultados de desempenho medidos.

## Objetivo
Converter imagens de recibos em registros estruturados, validar relações aritméticas suportadas e preservar evidências para revisão humana. A avaliação inicial usará o CORD v2 público; não comprova suporte a documentos fiscais brasileiros nem conferência entre nota e pedido.

## Fluxo planejado
Imagem → extração → validação do formato → verificações aritméticas → revisão humana → exportação.

## Documentação
- [Escopo e critérios de aceite](docs/scope.md)
- [Decisão de arquitetura](docs/architecture.md)
- [Proveniência e avaliação](docs/evaluation.md)
- [Regras de engenharia e contribuição](CONTRIBUTING.md)
- [Etapas e commits](docs/roadmap.md)

## Reprodução
Ambiente e dependências estão fixados no uv.lock. Os comandos de aquisição e verificação estão documentados abaixo.

## Fontes dos dados
- https://github.com/clovaai/cord
- https://huggingface.co/datasets/naver-clova-ix/cord-v2

O CORD pertence aos autores originais e é publicado sob CC BY 4.0. A licença dos dados é distinta da licença do código. Este pacote não contém os dados.

## Transparência
O estudo de caso deverá declarar a assistência de IA. Toda contribuição precisa ser compreendida, revisada e verificada pelo responsável pelo projeto. Resultados e alegações de implementação exigem evidências.

## Desenvolvimento e dados

Python 3.14 e uv. Instale o ambiente com `uv sync --locked`.

```powershell
uv run receipttrace prepare-cord
uv run receipttrace verify-sample
```

A aquisição baixa aproximadamente 490 MB. Apenas o primeiro arquivo de treino é utilizado na inspeção inicial; validação e teste ficam reservados. [Instruções e verificações](docs/development.md).

Implementado: aquisição com revisão e hash fixados, amostragem determinística, manifesto de proveniência, verificação local e testes de integridade. Extração, API e interface continuam pendentes.

[Relatório da inspeção inicial dos dados](docs/reports/cord-inspection.md).
