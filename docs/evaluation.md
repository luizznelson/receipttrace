# Dados e protocolo de avaliação

## Fonte e aquisição
CORD v2 oficial: https://huggingface.co/datasets/naver-clova-ix/cord-v2
Repositório dos autores: https://github.com/clovaai/cord
Licença declarada: CC BY 4.0. Conferir atribuição e termos na revisão exata adquirida.

Não confundir a coleção total descrita no artigo com o subconjunto público. Registrar as contagens efetivamente obtidas por divisão na inspeção.

## Manifesto obrigatório
Dataset, revisão imutável, URL de origem, data UTC de aquisição, divisão original, ID, SHA-256 do arquivo, licença e alterações locais. Preservar originais; dados derivados devem apontar para eles.

## Primeiro experimento
Inspecionar uma amostra determinística de 20 documentos de desenvolvimento, com IDs e semente registrados. Verificar cobertura das anotações, separadores numéricos, itens agrupados, legibilidade e campos ausentes. Isso é descoberta do formato, não benchmark final.

## Separação
Usar treino para desenvolvimento, validação para seleção de configuração e teste para avaliação final. Não ajustar prompts pelo teste. Verificar duplicatas antes de comparar abordagens e documentar qualquer desvio das divisões oficiais.

## Comparação justa
Mesmos documentos e campos elegíveis para OCR/regras e IA. Baseline OCR não recebe transcrições anotadas. Transformações que usam OCR de referência são experimentos separados, explicitamente identificados. Definir correspondência de itens e normalização antes de medir.

## Métricas propostas
- Acerto por campo após normalização documentada e taxa de falha por documento.
- Precisão, revocação e F1 de itens com algoritmo de correspondência publicado.
- Resultado de verificações aritméticas em casos aplicáveis, distinto de acerto da extração.
- Latência p50/p95 por documento, com ambiente e política de cache.
- Custo por documento, incluindo tentativas, modelo, tokens e preços datados.
- Frequência de revisão: medida por regras explícitas, sem confundir autoconfiança do modelo com probabilidade calibrada.

Incluir tamanho da amostra e contagens brutas. Reportar ausências, exclusões e erros. Ausência de resultado não deve melhorar artificialmente as métricas. Rótulos podem conter erros: correções curadas ficam versionadas e resultados oficiais e curados são apresentados separadamente.

## Registro por execução
run_id, data UTC, commit, estado de alterações locais, revisão dos dados, IDs avaliados, versão/hash do prompt, provedor/modelo e identificador exato disponível, parâmetros, dependências, resultado, erros, tentativas, duração e uso/custo. Variação do provedor pode impedir igualdade exata; preservar as saídas observadas e documentar essa limitação.

## Evidência
Resultados agregados, saídas por documento e exemplos de erro devem acompanhar o relatório. Gabaritos não são acessíveis ao extrator. Segredos nunca fazem parte dos registros.
