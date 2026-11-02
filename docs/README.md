# Como explorar o ReceiptTrace

A documentação acompanha a mesma história da aplicação: problema, experiência, resultado e implementação.

## Se você tem 5 minutos

1. Leia a seção 3 do [README](../README.md): o que foi medido e o que não foi.
2. Abra o [estudo de caso](case-study.md) para ver o problema e as decisões.
3. Veja [Arquitetura](architecture.md) e o fluxo em [Envio temporário](uploads.md).
4. Confira [Qualidade](quality.md) e rode os testes com o [guia de desenvolvimento](development.md).

## Por tema

| O que você quer entender? | Comece aqui |
| --- | --- |
| Qual problema motivou o projeto? | [Estudo de caso](case-study.md) e [perguntas de negócio](business-case.md) |
| Como experimentar e conferir um recibo? | [Interface e API](web.md) e [teste temporário](uploads.md) |
| Como publicar a demonstração? | [Implantação](deploy.md) |
| O que melhorou com IA e quais são os limites? | [Relatório do experimento](reports/gemini-development-20.md) |
| Como foram escolhidos os dados e calculados os acertos? | [Avaliação](evaluation.md) e [origem da amostra](reports/cord-inspection.md) |
| Por que o código foi organizado assim? | [Arquitetura](architecture.md) e [decisão da interface web](architecture-web.md) |
| Como dinheiro e correções são tratados? | [Domínio](domain.md) e [revisão local](review.md) |
| Como verificar o trabalho? | [Qualidade](quality.md), [desenvolvimento](development.md) e [segurança](security.md) |
| Como executar novas extrações? | [OCR local](ocr.md), [Gemini](gemini.md) e [adaptador OpenAI opcional](llm.md) |

## O que fica em cada lugar

`reports/` contém o experimento publicado, a origem dos dados e evidências relevantes. `reports/evidence/` preserva respostas e manifestos usados na avaliação. `contracts/` contém esquemas verificáveis da API e dos dados. `images/` e `media/` apresentam a experiência da aplicação (imagens e uma demonstração em vídeo).

As cópias em `src/receipttrace/webdata/` são necessárias à distribuição: permitem abrir a demonstração instalada sem baixar o dataset. Elas são verificadas por checksum. Não substituem as evidências do experimento.

Registros intermediários de implementação não fazem parte da apresentação atual. A evolução do código continua disponível no histórico Git; as verificações atuais podem ser reproduzidas pelos comandos dos guias.
