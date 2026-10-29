# OCR local: execução e avaliação

## Por que existe esta comparação

O OCR reconhece texto na imagem e usa regras para identificar os valores. Ele oferece uma referência local para verificar se a IA traz ganho de qualidade que justifique seu tempo e sua dependência de uma API.

Na amostra de desenvolvimento, o OCR recuperou corretamente 14 dos 19 totais anotados. Foi mais rápido que o Gemini, mas deixou mais campos sem resposta e confundiu dois totais. [Resultado do OCR](reports/ocr-baseline.md) · [Comparação com Gemini](reports/gemini-development-20.md).

## Instalar e executar

Na raiz do projeto, com Python 3.14 e uv, prepare a amostra conforme o [guia de desenvolvimento](development.md). Depois:

```powershell
uv sync --locked --extra ocr
uv run --extra ocr receipttrace extract-ocr --inputs data/processed/cord-inspection/inputs --output runs/ocr-my-run
uv run --extra ocr receipttrace evaluate-ocr --sample data/processed/cord-inspection --run runs/ocr-my-run --output runs/ocr-my-evaluation.json
```

Use diretórios e arquivos de saída novos. A dependência `ocr` é opcional; a validação do domínio e a reavaliação de respostas salvas não exigem instalar o motor.

## Motor e rastreabilidade

RapidOCR usa ONNX Runtime em CPU, com uma thread intra-op e inter-op. Os três modelos ONNX vêm do pacote fixado em `uv.lock` e têm caminhos explícitos. O manifesto registra versões, hashes dos modelos e da configuração, hashes do código e do lock, commit e alterações locais.

São modelos PP-OCR de uso geral, não treinados por este projeto nem validados para todos os idiomas e formatos. Licenças e atribuições de código e pesos pertencem aos respectivos autores. Os pesos não entram no Git. A inferência não usa uma API paga; o custo computacional local não foi estimado.

Referências dos mantenedores: [RapidOCR](https://github.com/RapidAI/RapidOCR) e [documentação de uso](https://github.com/RapidAI/RapidOCRDocs/blob/main/docs/install_usage/rapidocr/usage.en.md).

## Regras de extração e falhas

`extract-ocr` recebe apenas uma pasta com imagens PNG. Não recebe anotações. Salva texto, coordenadas, scores, linhas agrupadas, candidatos por campo, dados estruturados, validação e tempo. Scores do OCR não são probabilidades calibradas de acerto.

As regras procuram subtotal, total, imposto, serviço e desconto. `GRAND TOTAL` tem prioridade sobre `TOTAL`; candidatos de mesma prioridade com valores diferentes geram abstenção, ou seja, o campo fica sem resposta. Moeda e completude dos itens não são presumidas.

Itens só são propostos no formato simples quantidade + descrição + valor. Linhas compostas e outros alinhamentos frequentemente falham. Preço unitário e desconto ausentes não são preenchidos.

Uma falha em um documento gera `error` e permite continuar nos demais. Imagem sem texto gera `empty`. Falha de inicialização ou gravação pode interromper a execução; somente lotes com manifesto completo podem ser avaliados. Não há cache de resultados.

## O que a avaliação mede

O avaliador verifica hashes, IDs e imagem de origem antes de abrir os gabaritos. Mede cinco campos de totais, com comparação exata pela política `idr-grouped`. Desconto é comparado por magnitude.

- `exact_match_recall`: acertos divididos pelos documentos com referência numérica válida.
- Precisão das respostas anotadas: acertos divididos pela soma de acertos e valores incorretos.
- Falhas e campos sem resposta permanecem no denominador válido.
- Previsões sem anotação e referências inválidas são informadas separadamente.

Não há métrica de qualidade dos itens nem acurácia geral do recibo. Veja o [protocolo de avaliação](evaluation.md).

## Medição de tempo e publicação

O tempo por documento usa relógio monotônico e inclui hash, inferência, regras e validação. Exclui gravação e inicialização; a primeira inferência inclui o carregamento tardio dos modelos. Os percentis usam nearest rank, sem interpolação. Memória e custo de CPU/hospedagem não foram medidos.

O [relatório](reports/ocr-baseline.md) explica os resultados. A [evidência publicada](reports/evidence/ocr-baseline/manifest.json) preserva o manifesto e as saídas originais, incluindo o texto OCR. Não inclui imagens nem chaves. `runs/` continua fora do Git; mudanças nas saídas exigem nova avaliação.
