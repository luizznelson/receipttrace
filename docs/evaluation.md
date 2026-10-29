# Dados e método de avaliação

## O que a avaliação responde

A avaliação mede quais valores foram extraídos corretamente, em quais documentos houve erro e quanto tempo cada abordagem levou. Ela permite comparar OCR e IA sob as mesmas condições. Ainda não mede redução de trabalho humano nem qualidade em uma operação de empresa.

O [experimento atual](reports/gemini-development-20.md) usa 20 recibos de desenvolvimento. A avaliação final em dados reservados continua pendente.

## Origem dos dados

O projeto usa o [CORD v2 público](https://huggingface.co/datasets/naver-clova-ix/cord-v2), dos [autores do CORD](https://github.com/clovaai/cord), sob CC BY 4.0. A quantidade de documentos deve ser conferida na revisão adquirida; não se deve assumir que a coleção descrita no artigo inteiro está disponível no subconjunto público.

O manifesto registra dataset, revisão imutável, origem, data UTC, divisão, IDs, hashes SHA-256, licença e transformações locais. As imagens originais são preservadas. Resultados derivados apontam para a origem.

## Separação entre desenvolvimento e avaliação final

O treino é usado para desenvolver a solução; a validação, para escolher configurações; e o teste, para a avaliação final. Prompts e regras não devem ser ajustados pelo resultado do teste reservado. Duplicatas entre divisões devem ser investigadas antes da comparação final.

A amostra atual contém 20 documentos do primeiro arquivo de treino, com semente 42. Foi usada para conhecer os layouts e desenvolver a integração. Portanto, seus resultados não estimam de forma independente o desempenho em documentos novos.

## Como tornar a comparação justa

OCR e IA recebem as mesmas imagens. As respostas esperadas ficam disponíveis somente ao avaliador. O método de normalização e os campos avaliados precisam ser iguais nas duas abordagens.

Atualmente são avaliados total, subtotal, imposto, serviço e desconto. A comparação exige mesmo manifesto de amostra, IDs, hashes de imagem e quantidade de referências válidas por campo. Um documento que falha continua contado nos campos em que existe uma referência válida.

## Como interpretar os indicadores

| Indicador | Cálculo ou significado | Pergunta respondida |
|---|---|---|
| Acertos sobre referências válidas (`exact_match_recall`) | Corretos ÷ campos com referência numérica válida | Quanto do que podia ser conferido foi recuperado corretamente? |
| Precisão das respostas anotadas | Corretos ÷ (corretos + valores incorretos) | Entre os valores respondidos que podiam ser conferidos, quantos estavam certos? |
| Falhas por documento | Quantidade de resultados com erro técnico | O processamento terminou? |
| Mediana, ou p50 | Valor central dos tempos ordenados | Qual foi o tempo típico observado? |
| Percentil 95, ou p95 | Tempo na posição de 95% da amostra, por nearest rank | Até quanto demorou a maioria dos documentos? |
| Uso e custo estimado da API | Tokens informados e tarifas da configuração | Qual foi o uso conhecido e a estimativa sob essas tarifas? |

A comparação monetária é exata após normalização, sem tolerância, com a política `idr-grouped`. Descontos são comparados por magnitude. Campos sem anotação não contam como erros nem acertos; previsões nesses campos são informadas separadamente. Referências numéricas inválidas também são separadas do denominador válido.

Não há uma métrica geral de acerto do recibo. A qualidade dos itens ainda não foi implementada. Precisão, revocação e F1 de itens exigirão um método de correspondência definido antes da medição. A frequência e o tempo de revisão humana também permanecem pendentes.

## O que preservar em cada execução

Registre data UTC, commit, alterações locais, revisão dos dados, IDs, hashes do prompt e do esquema, provedor, modelo solicitado e identificador retornado quando disponível, parâmetros, dependências, resultados, erros, tentativas, duração e uso/custo. Registre também o escopo da medição de tempo: as etapas do OCR local e da API são diferentes.

Preserve as respostas observadas, pois uma nova inferência pode variar. Não trate estimativa de custo como fatura, nem um campo de confiança do modelo como probabilidade calibrada de acerto.

## Publicação e correções

O relatório apresenta contagens, resultados por documento, exemplos de falha e limitações. A ausência de resposta não pode melhorar artificialmente o resultado. Credenciais ficam fora dos registros.

Se uma anotação parecer errada ou incompleta, documente o caso. Correções revisadas devem ser versionadas separadamente, com resultados oficiais e corrigidos apresentados de forma distinta. O gabarito não deve ser alterado para favorecer o extrator.
