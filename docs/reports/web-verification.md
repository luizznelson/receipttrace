# Verificação da aplicação web — 29/10/2026

## Resultado da entrega

A aplicação local permite entender o problema, comparar OCR e IA em três recibos reais e registrar revisões com histórico em PT-BR ou inglês. Os indicadores vêm do lote de 20 documentos, preservando o recorte e as limitações da avaliação original.

A entrega inclui FastAPI, arquivos de interface locais, contrato OpenAPI e exemplos públicos com atribuição. Não exige chave de API nem download do dataset completo para abrir a demonstração. O uso com várias pessoas em uma operação e a hospedagem continuam pendentes.

## Verificações automatizadas

- 173 testes Python aprovados, incluindo 22 casos da API.
- Oito testes JavaScript aprovados: idiomas, rótulos, estados distintos, números de indicadores e preservação do texto monetário.
- Ruff: análise e formatação aprovadas; mypy: 16 módulos de origem sem erros.
- Sintaxe dos quatro módulos JavaScript verificada; Prettier 3.9.10 aprovado, com versão fixada em `package-lock.json`.
- Testes de API cobrem comparação com evidência salva, imagem e hashes, revisão, conclusão, conflito 409, exportação, modo de consulta, origem/host locais, pedidos inválidos e integridade do histórico.
- Os 49 recursos da demonstração foram verificados por checksum dentro do wheel; essa checagem foi adicionada à CI. O wheel final foi construído e aberto fora do checkout. A aplicação importada do pacote serviu página, JavaScript, indicadores e imagem, com três PNGs e sem `.env` ou banco incluídos.

Ambiente: Python 3.14; Node v24.14.1; FastAPI 0.162.0, Starlette 1.10.0, Uvicorn 0.54.0 e httpx2 2.16.0, fixados em `uv.lock`.

## O que foi conferido no navegador

O teste automatizado de interface abriu a revisão OCR do exemplo 0006, preservou `62,000` como extração original e registrou `61,799` na revisão. Trocar para inglês preservou valor, responsável e motivo ainda não salvos. A conclusão ficou bloqueada sem reconhecimento dos cálculos não verificados; depois da ação explícita, a revisão foi concluída e a aritmética permaneceu `not_checked`.

O histórico foi recuperado ao reabrir a revisão e seu download JSON foi concluído. Uma observação contendo `<b>texto literal</b>` apareceu como texto, sem criar elemento HTML.

No exemplo 0059, duas sessões abriram a versão 0. A sessão B salvou `25,000`. O envio da sessão A foi recusado, seu rascunho `24,999` foi preservado e o botão de salvar ficou bloqueado. Recarregar com descarte explícito recuperou `25,000` na versão 1.

Os responsáveis e motivos desses testes identificam automação de QA; não são registros de revisão realizada por pessoas nem medições de produtividade.

## Apresentação e modo de consulta

A apresentação foi conferida em desktop e em um viewport de celular de 390 × 844. Um excesso de largura no hero foi corrigido; a área útil de 375 px e a largura total do documento ficaram iguais. Em desktop, ambas mediram 1.265 px. Houve verificação básica de navegação por teclado e foco visível, sem auditoria completa de acessibilidade.

O modo somente leitura mostrou o aviso de consulta e ocultou ações de revisão. Não criou o banco indicado para o teste. Os testes de API também confirmaram que esse modo recusa leitura e alteração de revisões.

[Captura da apresentação](../images/receipttrace-overview.jpg) · [Registro das verificações](web-verification.json) · [Como executar](../web.md)

## O que foi preservado e o que fica pendente

As extrações e métricas originais não foram reescritas. As imagens incluídas preservam os bytes originais do CORD e seus hashes, com atribuição CC BY 4.0. Revisões dos testes ficam em banco separado em `runs/`, fora do Git.

Não houve nova inferência, uso de chave, envio de recibos a um provedor, execução da CI no GitHub, commit, push ou deploy nesta etapa. A CI foi atualizada, mas sua execução remota ainda precisa ser confirmada. Os servidores temporários de QA são encerrados ao concluir os testes; a aplicação pode ser aberta pelo comando documentado.
