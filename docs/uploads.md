# Testar um recibo próprio

O envio permite testar a leitura de uma imagem nova sem chave de API. O OCR local procura cinco campos: total, subtotal, imposto, serviço e desconto. A tela mostra a imagem, a leitura original, as linhas usadas como evidência e campos para correção.

Os novos testes não possuem gabarito e não entram nos indicadores do estudo CORD. “Campos identificados” é uma contagem de preenchimento, não uma nota de acerto.

## Como iniciar

Encerre o servidor anterior com Ctrl+C. Na pasta do projeto:

```powershell
uv sync --locked --extra web --extra ocr
uv run --no-sync receipttrace serve --uploads
```

Abra [http://127.0.0.1:8000/#try](http://127.0.0.1:8000/#try). Se o navegador ainda mostrar a interface anterior, recarregue a página. Sem `--uploads`, os exemplos continuam disponíveis e a tela explica que o envio está desativado.

Para habilitar o teste temporário em uma instância pública, mantenha as revisões do banco bloqueadas:

```powershell
uv run --no-sync receipttrace serve --read-only --uploads --host 0.0.0.0
```

Esse comando não publica o projeto por conta própria. A hospedagem ainda precisa ser configurada e testada com HTTPS, limites de memória/CPU e tráfego. Não há cobrança por chamada de API neste fluxo; os recursos de computação e hospedagem têm condições próprias.

## Jornada da pessoa

1. Escolher uma imagem PNG ou JPG, sem dados pessoais ou sensíveis.
2. Escolher como os números aparecem no documento. O idioma da página não altera a interpretação dos valores.
3. Confirmar o aviso e selecionar “Ler meu recibo”. A tela mostra o tempo decorrido durante o recebimento e a leitura, sem porcentagens fictícias.
4. Conferir a imagem e os campos. Valores ausentes ou conflitantes ficam vazios; linhas reconhecidas podem ser consultadas.
5. Corrigir os valores necessários e registrar o motivo. Selecionar “Conferir formato e cálculos” para avaliar a versão atual. O resultado mostra problemas de formato e divergências, além do que não pôde ser verificado.
6. Baixar o JSON com a extração original, a versão atual, as alterações antes/depois, o motivo e os horários desta sessão. Usar “Limpar este teste” para remover o conteúdo da interface.

PT-BR e inglês preservam o arquivo selecionado, as correções e o motivo. O navegador avisa ao sair quando há correções ainda não exportadas. O registro desta aba não autentica quem conferiu e não é armazenado no banco de revisões dos exemplos.

## Formatos de números

| Seleção | Exemplos | Política técnica |
| --- | --- | --- |
| Vírgula decimal | `12,50`, `1.234,56`, `R$ 1.234,56` | `brl-grouped` |
| Ponto decimal | `12.50`, `1,234.56`, `$ 1,234.56` | `usd-grouped` |
| Sem centavos | `61,799` ou `61.799`, ambos representando `61799` | `idr-grouped` |

São convenções numéricas explícitas; não determinam a moeda do documento. As regras de leitura ao vivo são `upload-rules-1`, separadas das regras históricas `ocr-rules-1`. Os valores mantêm sua escrita original e a normalização usa Decimal.

## Proteções e retenção

- Corpo da imagem: até 8 MiB; PNG ou JPEG confirmado pelo decodificador, não apenas pela extensão. Imagens animadas ou com múltiplos quadros são recusadas.
- Resolução: até 12 milhões de pixels, até 12.000 pixels por lado, mínimo de 32 pixels por lado. As dimensões são verificadas antes da leitura completa dos pixels.
- Preparação: orientação EXIF aplicada, metadados removidos e redução proporcional para até 2.400 pixels por lado antes do OCR. A tela informa quando houve redução.
- Recebimento: até 10 segundos; conferência transitória de campos: até 256 KiB, campos limitados a 64 caracteres, sem edição ou injeção de itens.
- Execução: processo separado, uma imagem por vez e até 10 tentativas por minuto **por processo do servidor**, compartilhadas entre visitantes. O OCR é interrompido após 60 segundos. A interface aguarda até 70 segundos e não repete automaticamente a requisição.
- O processo recebe somente as variáveis de ambiente necessárias; chaves Gemini/OpenAI não são herdadas. O código usa modelos locais já instalados e não acessa provedores de IA.
- A aplicação não grava imagem nem texto recebido no sistema de arquivos, banco ou logs. O resultado é devolvido à mesma requisição e permanece na memória da aba. O JSON só é gravado no computador quando a pessoa solicita o download.
- A imagem é identificada por SHA-256. O nome informado pelo visitante não vira caminho no servidor. Não há endpoint de consulta de imagens ou resultados enviados por outras pessoas.

O processo separado não é um isolamento de segurança do sistema operacional nem um limite rígido de RAM. O limite de concorrência é local ao processo e não é uma cota por pessoa nem defesa contra DDoS. O encerramento do navegador pode deixar o OCR terminando no servidor até o limite de tempo; não há tarefa persistente nem consulta posterior. A hospedagem deve impedir gravação/captura de corpos pelo proxy e configurar seus próprios limites e logs. Memória virtual, navegador e infraestrutura não estão cobertos por uma garantia de apagamento seguro.

## O que o resultado não comprova

O OCR pode errar letras e números. As regras reconhecem rótulos comuns em português, inglês e os rótulos indonésios usados no estudo; isso não comprova suporte geral a esses idiomas. Modelos e regras ainda não foram avaliados em uma amostra independente de recibos brasileiros.

Itens não são estruturados no teste ao vivo. A soma dos itens fica sem conferência. Para verificar `subtotal − desconto + imposto + serviço = total`, todos os cinco componentes precisam estar explícitos e válidos. Campo ausente não é convertido em zero. Uma igualdade aritmética ou uma correção feita no navegador não aprova pagamento, documento fiscal ou autenticidade.

## API e responsabilidades

| Rota | Uso |
| --- | --- |
| `GET /api/uploads/capabilities` | Disponibilidade e limites; não inicializa o motor OCR. |
| `POST /api/uploads?policy=brl-grouped` | Corpo binário PNG/JPEG; devolve leitura, evidências e validação. |
| `POST /api/uploads/validate` | JSON transitório com os cinco campos e política; reavalia sem salvar. |

`upload_worker.py` verifica e prepara a imagem e executa o OCR. `upload_rules.py` seleciona campos de forma conservadora. `uploads.py` controla processo, concorrência e tempo. `web_boundary.py` aplica origem, formato e tamanho. `upload.js` apresenta a jornada, correções e exportação; `upload-client.js` contém o contrato de envio e as diferenças entre original e versão atual.

O [contrato OpenAPI](contracts/web-openapi.json), os testes `test_uploads.py` e `upload-client.test.mjs` e o [relatório desta entrega](reports/uploads-verification.md) permitem conferir a implementação.
