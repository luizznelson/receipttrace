# Segurança e tratamento de falhas

O ReceiptTrace foi projetado para dois usos: revisão no computador do mantenedor e demonstração pública somente para leitura. A revisão de 30/10/2026 corrigiu falhas confirmadas e acrescentou testes. A etapa seguinte adicionou envio temporário de PNG/JPEG, habilitado explicitamente; seus controles e limites estão no [guia de uploads](uploads.md). Ela não equivale a um teste de invasão nem garante ausência de vulnerabilidades.

## O que está protegido

| Situação | Comportamento esperado |
| --- | --- |
| Entrada inválida | A API rejeita campos fora do contrato sem devolver o conteúdo recebido. |
| Corpo excessivo ou lento | Correções e validações JSON têm limite de 256 KiB; imagens habilitadas têm limite de 8 MiB. O recebimento tem limite de 10 segundos, antes de acessar o banco. O limite vale também para transferência em partes. |
| Falha inesperada | Resposta JSON genérica com identificador da requisição. O registro da aplicação guarda identificador e classe da exceção, sem mensagem, corpo ou credenciais. |
| Falha de armazenamento | Resposta 503; correções usam transações SQLite e controle de versão para evitar sobrescrever outra revisão. |
| Evidência alterada ou ausente | Imagens, extrações e relatórios solicitados são conferidos por SHA-256; uma divergência impede a entrega daquele arquivo. O catálogo é conferido ao iniciar. |
| Resposta perdida durante uma alteração | A interface aguarda até 15 segundos. Erro de rede, resposta inválida ou erro 5xx bloqueia novas alterações da revisão aberta até recarregar o estado. Não há repetição automática de escrita. |
| Tentativa de escrita em outra origem | A revisão local exige host de loopback, JSON e origem compatível quando o cabeçalho Origin está presente. Isso não substitui autenticação. |
| Demonstração pública | O modo somente leitura bloqueia escritas no banco e acesso às revisões locais. Por padrão, não permite upload. Com `--uploads`, executa OCR local temporário; as revisões do banco continuam inacessíveis. A leitura por IA só existe se a hospedagem configurar chave e variáveis explícitas; a chave fica apenas no servidor e não é herdada pelo processo de OCR. |
| Conteúdo malicioso na tela | Valores são inseridos como texto. CSP limita recursos à própria origem e impede incorporação em páginas externas. A API usa no-store, nosniff e identificador da requisição, inclusive nos erros. |

Erros esperados distinguem entrada inválida, recurso inexistente, conflito de versão, falha de integridade e armazenamento indisponível. Erros de programação não são tratados genericamente como culpa do usuário.

## Credenciais e dependências

A chave de API fica no `.env` local, excluído do Git. A demonstração funciona com resultados salvos e não precisa dessa chave. Não coloque `.env`, bancos de revisão, credenciais ou cópias de dados privados em commits ou imagens de implantação. A conferência desta revisão encontrou somente `.env.example` entre os nomes de arquivos de ambiente rastreados; não foi uma auditoria de todo o histórico Git.

O Pillow foi atualizado de 12.3.0 para 13.0.0 após alertas do pip-audit. A consulta após a atualização não encontrou vulnerabilidades conhecidas nas dependências Python consultadas; o npm audit também não encontrou alertas. Esses resultados dependem das bases disponíveis na data da consulta e precisam ser renovados. Veja o [relatório e os comandos reproduzíveis](reports/security-audit-2026-10-30.md).

Para aplicar a atualização ao ambiente habitual, encerre o servidor local, execute `uv sync --locked --extra web` na pasta do projeto e inicie novamente com o comando usado no [guia web](web.md). Instale também os extras de OCR ou de provedores caso precise executar novas extrações. A auditoria usou um ambiente isolado para preservar o servidor que já estava aberto.

## Limites antes da publicação

- Publique a demonstração com revisões do banco somente em modo de leitura; o envio temporário pode ser habilitado separadamente com `--uploads`. Revisões com escrita ainda não têm login, autorização por usuário, sessões ou separação entre usuários.
- Configure HTTPS e limites de tráfego/conexões na hospedagem. Não foram implementadas proteção contra DDoS, cotas por visitante ou monitoração operacional com alertas.
- Os hashes identificam divergências em relação à evidência esperada. Eles não são assinatura digital nem registro externo: alguém com controle de todo o banco ou pacote pode substituir também os hashes.
- **Leitura por IA (Gemini, plano gratuito).** Riscos conhecidos: (1) a imagem sai do servidor e, pelos termos do plano gratuito, o Google pode usar o conteúdo para melhorar produtos; mitigação: consentimento por leitura, aviso na tela, `RECEIPTTRACE_GEMINI_FREE_TIER=confirmed` e orientação para não enviar dados pessoais; (2) abuso de cota; mitigação: limites por dia, por visitante, por minuto, simultaneidade e pausa após erro do provedor, sempre com fallback ao OCR; (3) as cotas ficam em memória e zeram em reinício ou suspensão da hospedagem, então o limite diário é aproximado; (4) a identificação do visitante depende de `RECEIPTTRACE_PROXY_HOPS` correto, que precisa ser verificado na hospedagem real; (5) a chave vale para o plano gratuito, mas deve ser tratada como segredo e revogada se vazar. Nada disso foi exercitado com chamadas reais ao provedor nesta revisão; os testes usam respostas simuladas.
- O upload opcional aceita somente imagens com limites e processamento temporário, conforme o [guia](uploads.md). PDFs e arquivos arbitrários não são aceitos. O processo separado não substitui isolamento do sistema operacional ou limites de RAM/CPU da hospedagem.
- Os logs genéricos descritos acima são os erros da aplicação. Logs do servidor, proxy e hospedagem precisam de configuração própria; não envie segredos em URLs.
- Backups, recuperação de desastre, segurança do sistema operacional e revisão independente de segurança ficam fora desta entrega.

Uma revisão concluída continua sem equivaler a aprovação de pagamento, validação fiscal ou conferência de cálculos sem os componentes necessários.
