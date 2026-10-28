# OCR local e avaliação independente

## Instalação
Na raiz do projeto, com Python 3.14 e uv:
```powershell
uv sync --locked --extra ocr
uv run --extra ocr receipttrace extract-ocr --inputs data/processed/cord-inspection/inputs --output runs/ocr-my-run
uv run --extra ocr receipttrace evaluate-ocr --sample data/processed/cord-inspection --run runs/ocr-my-run --output runs/ocr-my-evaluation.json
```
Obtenha a amostra com `prepare-cord` antes. Diretórios/arquivos de saída devem ser novos. `ocr` é uma dependência opcional; o domínio e os testes não exigem instalar o motor.

## Motor
RapidOCR com ONNX Runtime em CPU, uma thread intra/inter-op. São usados os três modelos ONNX incluídos no pacote fixado no uv.lock, com caminhos explícitos. Versão, hashes dos modelos e da configuração, hashes do código/lock, commit e estado de alterações locais ficam no manifesto de execução. Sem API de inferência paga.

Referências dos mantenedores:
- https://github.com/RapidAI/RapidOCR
- https://github.com/RapidAI/RapidOCRDocs/blob/main/docs/install_usage/rapidocr/usage.en.md

O motor usa modelos PP-OCR de uso geral, não foi treinado por este projeto nem validado para todas as línguas/formatos. Licenças e atribuições de código e pesos são próprias dos respectivos autores. Os pesos não são copiados para o Git.

## Separação e evidências
O comando `extract-ocr` recebe somente um diretório de imagens PNG. Não recebe caminhos de anotações. Salva texto reconhecido, coordenadas, scores, linhas agrupadas, candidatos de cada campo, dados estruturados, validação e duração. Os scores não são probabilidades calibradas de acerto.

O extrator não infere moeda nem completude dos itens. Regras suportam subtotal, total, imposto, serviço e desconto. GRAND TOTAL tem prioridade sobre TOTAL; candidatos de mesmo nível com valores diferentes geram abstenção. Itens só são propostos no formato simples quantidade + descrição + valor. Layouts distintos, multilinhas e valores alinhados em outra linha frequentemente falham. Preço unitário e desconto ausente do item não são presumidos.

Falha por documento é registrada como error e não interrompe os demais. OCR sem texto gera empty. Falha na inicialização ou escrita pode interromper a execução; só execuções com manifesto completo são avaliáveis. Não há cache de resultados.

## Avaliação
O comando de avaliação verifica hashes da amostra e dos resultados, correspondência dos IDs e imagem de origem antes de abrir os gabaritos. Mede apenas os cinco campos de totais suportados. Comparação numérica exata sob política idr-grouped; desconto é comparado por magnitude.

- Recall exato: corretos / documentos com referência numérica válida.
- Precisão em respostas anotadas: corretos / (corretos + valores incorretos).
- Campo de referência ausente não é um negativo: predições nesses campos são reportadas separadamente.
- Falhas e campos sem resposta permanecem no denominador anotado.
- Gabarito numérico inválido é contado explicitamente, separado do denominador válido.

A avaliação de itens ainda não existe. Não se deve resumir essas métricas como acurácia geral do recibo ou qualidade de todos os itens.

Latência usa relógio monotônico por documento; inclui hash, inferência, regras e validação, exclui escrita da saída e inicialização. A primeira inferência inclui o carregamento preguiçoso dos modelos. Percentis usam nearest rank, sem interpolação. Não foi medido consumo de memória ou custo de CPU/hospedagem.

## Publicação
`runs/` permanece fora do Git. O relatório agregado e valores dos campos avaliados ficam em `docs/reports/ocr-baseline.json`, com o resumo em `ocr-baseline.md`. Nenhum texto OCR completo ou imagem foi incluído nesses relatórios. O manifesto completo do run permanece local; seu hash é publicado para auditoria. Alterar os arquivos exige nova avaliação.
