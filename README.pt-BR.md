# ReceiptTrace

Extração de recibos com avaliação rastreável e revisão humana.

[English](README.md)

## Estado atual
Etapa de especificação. Extrator, benchmark, API e interface ainda não foram implementados. Não há resultados de desempenho medidos.

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
Ambiente, dependências e comandos executáveis serão documentados e fixados com o primeiro pipeline de dados. Esta fundação requer apenas um leitor de Markdown.

## Fontes dos dados
- https://github.com/clovaai/cord
- https://huggingface.co/datasets/naver-clova-ix/cord-v2

O CORD pertence aos autores originais e é publicado sob CC BY 4.0. A licença dos dados é distinta da licença do código. Este pacote não contém os dados.

## Transparência
O estudo de caso deverá declarar a assistência de IA. Toda contribuição precisa ser compreendida, revisada e verificada pelo responsável pelo projeto. Resultados e alegações de implementação exigem evidências.
