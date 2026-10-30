# Implantação (Render, plano gratuito)

Roteiro para publicar a demonstração somente leitura com envio de recibos. **Nada aqui foi executado em hospedagem real**; os passos abaixo precisam ser conferidos por quem publica.

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
- **Imagem Docker:** as versões fixadas de Python e uv no `Dockerfile` não foram verificadas aqui; o build ainda não foi executado.
- **Custos e termos:** acompanhe os limites do plano gratuito no Google AI Studio; se a chave vazar, revogue e gere outra.
- **Licença:** o repositório ainda depende da decisão do mantenedor sobre a licença.
