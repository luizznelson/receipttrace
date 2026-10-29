# ReceiptTrace

**Configuração da chave:** abra `.env` na raiz, preencha `GEMINI_API_KEY=` com sua chave e salve. A leitura é automática e o arquivo fica fora do Git. [Guia Gemini](docs/gemini.md).


Extração de recibos com avaliação rastreável e revisão humana.

[English](README.en.md)

## Estado atual
Aquisição de dados, validação do domínio, OCR local e extração com Gemini implementados e avaliados em 20 recibos reais do CORD v2. Resultados por documento e evidências de execução estão publicados. API da aplicação, revisão humana e interface ainda estão pendentes.

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

Implementado: aquisição com revisão e hash fixados, amostragem determinística, manifesto de proveniência, verificação local e testes de integridade. OCR e Gemini avaliados na mesma amostra de desenvolvimento; API da aplicação e interface continuam pendentes.

[Relatório da inspeção inicial dos dados](docs/reports/cord-inspection.md).

## Esquema e validação

Contratos estritos, preservação do texto original e regras monetárias com Decimal estão implementados. [Políticas e limites](docs/domain.md).

```powershell
uv run receipttrace validate-receipt examples/synthetic-receipt.json --policy idr-grouped
```

Este comando valida dados estruturados. A extração de imagens é realizada pelos comandos de OCR ou Gemini descritos abaixo.

## Extração OCR e medição inicial

OCR local em CPU e avaliação independente implementados. [Como executar e limites](docs/ocr.md). Na amostra de desenvolvimento: total correto em 14 de 19 documentos anotados. Esse resultado não mede todos os campos nem representa teste reservado. [Relatório completo](docs/reports/ocr-baseline.md).

## Integração com IA

Extração por visão com saída estruturada, planejamento offline, reserva de orçamento e comparação com o OCR implementados. [Configuração e limites](docs/llm.md). Gemini Flash-Lite avaliado nos 20 documentos da amostra de desenvolvimento. [Relatório e reprodução](docs/reports/gemini-development-20.md).

## IA com API gratuita

O caminho recomendado agora é Gemini 3.5 Flash-Lite, usando um projeto Free Tier **sem faturamento ativado**. [Configuração e execução](docs/gemini.md). A configuração de exemplo já usa Gemini e valores zero; é necessário confirmar o plano gratuito e configurar GEMINI_API_KEY localmente. Sem fallback pago. Avaliação dos 20 recibos concluída; os resultados abaixo descrevem esta amostra de desenvolvimento.

## Resultados em dados reais

Mesmos 20 recibos públicos para OCR e Gemini 3.5 Flash-Lite; números abaixo são campos corretos sobre referências válidas.

| Campo | OCR local | Gemini |
|---|---:|---:|
| total | 14/19 | 19/19 |
| subtotal | 9/14 | 14/14 |
| tax | 7/11 | 11/11 |

Gemini: 20/20 extrações concluídas tecnicamente; isso não comprova acerto de todos os campos. Latência p50 8.33 s e p95 22.52 s, incluindo pré-contagem remota e inferência, sem pausas entre documentos. Custo estimado conhecido de API: USD 0 sob a configuração Free Tier confirmada, sem faturamento ativado; não é fatura.

Amostra pequena de treino, sem teste reservado e sem métricas de itens. Serviço tem uma única referência; desconto não possui referência válida. [Relatório com erros, limites e comandos de reprodução](docs/reports/gemini-development-20.md) · [Resultados por documento](docs/reports/gemini-development-20.json) · [Comparação OCR/Gemini](docs/reports/ocr-vs-gemini-development-20.json). As evidências preservadas permitem recalcular as métricas sem chamar a API.
