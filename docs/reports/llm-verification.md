# Verificação da integração LLM — 28/10/2026

## Executado
- Instalação básica: 93 testes aprovados; módulo de testes do SDK ignorado pela ausência da dependência opcional.
- Instalação com extras llm e ocr: 95 testes aprovados.
- Ruff: formatação e análise aprovadas.
- mypy: 11 módulos de origem verificados nas duas configurações.
- Transporte HTTP simulado do SDK: imagem, esquema estruturado, uso de tokens, store=false e timeout sem retentativa verificados, sem tráfego externo.
- Planejamento offline dos 20 recibos reais: concluído com configuração sintética explicitamente identificada em runs/llm-offline-smoke-config.json. Nenhuma tarifa ou modelo desse fixture deve ser usado como recomendação real.
- Wheel construído e presença do prompt versionado confirmada.

## Evidências funcionais dos testes
Reservas insuficientes e excesso de tokens impedem inferência. Timeout sem uso conhecido interrompe novas chamadas e não registra mensagem de exceção do provedor. Recusas, respostas incompletas e contratos inválidos geram erro. Comparação exige mesma amostra e denominadores. O ID é local e a completude de itens não é certificada.

## Não executado
Nenhuma chamada real de contagem ou inferência à API. Nenhuma comparação real OCR versus LLM, resultado de qualidade de IA ou custo faturado. A credencial não estava configurada. Modelo, tarifas e orçamento reais permanecem pendentes. CI remota, commit, push e deploy não foram realizados nesta etapa.

## Referências
[Configuração e limites](../llm.md). O arquivo de exemplo em examples/llm-config.example.json contém placeholders inválidos de propósito e exige edição antes de qualquer uso real.

## Atualização posterior
A configuração principal passou a ser Gemini Free Tier. Os placeholders pagos descritos acima estão agora em examples/openai-config.example.json. Consulte gemini-verification.md para o estado da integração gratuita.
