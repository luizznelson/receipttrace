# ReceiptTrace

Extração de recibos com avaliação rastreável e revisão humana.

[English](README.en.md)

## Estado atual
Aquisição de dados e validação do domínio implementadas. OCR inicial e avaliação dos campos de totais implementados. Integração LLM implementada, sem execução real. API da aplicação e interface ainda estão pendentes. Não há resultados de desempenho medidos.

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

Implementado: aquisição com revisão e hash fixados, amostragem determinística, manifesto de proveniência, verificação local e testes de integridade. Integração LLM disponível sem medição real; API da aplicação e interface continuam pendentes.

[Relatório da inspeção inicial dos dados](docs/reports/cord-inspection.md).

## Esquema e validação

Contratos estritos, preservação do texto original e regras monetárias com Decimal estão implementados. [Políticas e limites](docs/domain.md).

```powershell
uv run receipttrace validate-receipt examples/synthetic-receipt.json --policy idr-grouped
```

Este comando valida dados estruturados; ainda não extrai informações de imagens.

## Extração OCR e medição inicial

OCR local em CPU e avaliação independente implementados. [Como executar e limites](docs/ocr.md). Na amostra de desenvolvimento: total correto em 14 de 19 documentos anotados. Esse resultado não mede todos os campos nem representa teste reservado. [Relatório completo](docs/reports/ocr-baseline.md).

## Integração com IA

Extração por visão com saída estruturada, planejamento offline, reserva de orçamento e comparação com o OCR implementados. [Configuração e limites](docs/llm.md). A execução real está pendente de chave, modelo e orçamento; não há resultado medido de IA.
