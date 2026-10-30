# Contribuição, revisão e comunicação

Uma entrega deve ser fácil de entender, verificar e manter. Mudanças pequenas e justificadas ajudam a identificar o que mudou, por que mudou e qual evidência sustenta o resultado.

## Padrão dos textos

O README e os resumos dos relatórios devem permitir que uma pessoa de gestão entenda o problema, o resultado e os limites sem precisar conhecer a implementação. Os guias técnicos devem permitir que uma pessoa de engenharia reproduza o trabalho e avalie as decisões.

- Comece pelo problema resolvido ou pelo resultado observado. Depois explique como ele foi obtido.
- Use frases diretas e palavras conhecidas. Explique uma sigla ou indicador na primeira ocorrência.
- Apresente números com contexto: “19 de 19 totais corretos nesta amostra”, em vez de “100% de acurácia”.
- Diferencie objetivo de benefício comprovado. Não declare economia de tempo, redução de custo operacional ou uso em produção sem medição.
- Explique o que cada resultado permite decidir e o que ainda precisa ser validado.
- Nos guias técnicos, preserve nomes de comandos, campos, parâmetros e estados. Explique o comportamento e o motivo da escolha.
- Identifique registros históricos. Uma limitação de uma etapa anterior não deve parecer o estado atual do produto.
- Mantenha o README principal em PT-BR e o secundário em inglês, com os mesmos números, estágio e limites.

## Apresentação do produto

O [caso de negócio](docs/business-case.md) define problema, público, perguntas e evidências. O [roteiro da interface](docs/case-study.md) define a ordem de apresentação, os estados e o vocabulário PT-BR/EN. Revise esses documentos ao mudar o escopo ou a evidência disponível.

Todo indicador visível deve identificar sua fonte e seu recorte. Não transforme sucesso técnico em aprovação financeira nem uma hipótese de produtividade em benefício medido.

## Antes de concluir uma entrega

- Conferir os critérios de aceite aplicáveis e os limites conhecidos.
- Executar as verificações relevantes e registrar os resultados, incluindo o que não foi executado.
- Revisar as diferenças dos arquivos, os dados publicados e a ausência de credenciais.
- Atualizar os guias e os resultados que dependem da mudança.
- Declarar a assistência de IA e revisar seu conteúdo. O responsável pelo projeto deve compreender a contribuição.

## Verificações técnicas

Ruff verifica formatação e estilo; mypy verifica tipos; pytest executa os testes. As dependências estão fixadas em `uv.lock`. O workflow de integração contínua executa essas verificações no GitHub; sua execução remota deve ser confirmada separadamente. Veja o [guia de desenvolvimento](docs/development.md).

Os testes cobrem regras e falhas relevantes, como valores monetários, campos ausentes, saídas inválidas e interrupções da API. A avaliação da qualidade da IA usa dados reais e é apresentada separadamente dos testes automatizados.

## Commits

O proprietário revisa as entregas e faz os commits. Use mensagens claras em português, no imperativo, com os prefixos `docs:`, `feat:`, `fix:`, `test:` ou `chore:`. A mensagem deve descrever uma mudança real e coerente. Não crie commits vazios nem divida arquivos artificialmente para aparentar atividade.

## Licenciamento

A licença do código ainda precisa ser escolhida pelo proprietário. Os dados têm licença e atribuição próprias. Não inclua datasets inteiros no Git; publique somente as evidências necessárias, com a origem identificada.
