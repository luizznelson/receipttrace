# Implantação (Render, plano gratuito)

Roteiro para publicar a demonstração somente leitura com envio de recibos. A demonstração publicada está em https://receipttrace.onrender.com.

## Registro do primeiro deploy (30/10/2026)

- Serviço criado no Render (região Ohio, plano gratuito) a partir deste repositório e do `Dockerfile`. O build funcionou, o que confirma as imagens `python:3.14.3-slim` e `uv:0.12.5`.
- A primeira inicialização falhou: `DemoIntegrityError`. Os hashes de `checksums.json` foram calculados com final de linha CRLF (Windows) e o Git guardava LF, então o clone em Linux não batia (47 de 50 arquivos).
- Correção: `.gitattributes` com `-text` para `src/receipttrace/webdata/` e `docs/reports/`, preservando os bytes exatos. Depois disso o serviço ficou no ar e a checagem `/api/health` passou a responder 200.
- Lição: dados verificados por hash não podem passar por conversão de final de linha.

## O que sobe

- Imagem Docker (`Dockerfile`) com a interface, a API e o OCR local.
- Modo somente leitura: o banco de revisões fica bloqueado.
- Envio de recibos habilitado; leitura por IA habilitada se as variáveis abaixo estiverem definidas.
- `render.yaml` descreve o serviço (plano gratuito, checagem em `/api/health`).

## Passo a passo

1. No Render, crie um *Blueprint* apontando para o repositório. Ele lê `render.yaml`.
2. No painel (nunca no repositório, nunca em conversa), preencha:
   - `GEMINI_API_KEY`: chave do Google AI Studio **do plano gratuito**.
   - `RECEIPTTRACE_GEMINI_FREE_TIER`: digite `confirmed` somente depois de ler os termos vigentes do plano gratuito.
3. Aguarde o build. Abra `/api/health` e `/api/uploads/capabilities`; `engines.gemini.available` deve ser `true`.
4. Teste um recibo sintético (sem dados pessoais) com cada método e simule o fallback desligando a chave.

## Conferências pendentes antes de divulgar

- **Proxy:** `RECEIPTTRACE_PROXY_HOPS=1` é uma suposição para o Render. Envie requisições de duas redes diferentes e confirme que contam como visitantes distintos; tente forjar `X-Forwarded-For` e confirme que não burla o limite por visitante.
- **Memória:** o plano gratuito tem 512 MB. Meça com `docker run --memory=512m` enviando imagens grandes (12 MP) pelos dois métodos.
- **Suspensão:** o serviço dorme após 15 min sem tráfego; a primeira visita demora e as cotas em memória são zeradas.
- **Consumo real:** o build e a inicialização funcionaram no Render, mas o consumo real de memória com imagens grandes ainda não foi medido; acompanhe a aba Metrics do serviço.
- **Custos e termos:** acompanhe os limites do plano gratuito no Google AI Studio; se a chave vazar, revogue e gere outra.
- **Licença:** o repositório ainda depende da decisão do mantenedor sobre a licença.
