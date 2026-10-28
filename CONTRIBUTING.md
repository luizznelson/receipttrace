# Desenvolvimento e revisão

## Princípios
Mudanças pequenas e explicáveis. Diagnóstico antes de correção. Nenhum resultado inventado. Documentar limitações e contribuição de IA.

## Antes de concluir uma etapa
- Verificar os critérios de aceite aplicáveis.
- Executar testes relevantes e registrar os comandos e resultados.
- Informar explicitamente verificações não executadas ou bloqueadas.
- Revisar diff, dados publicados e possíveis segredos.
- Atualizar documentação quando o comportamento mudar.

## Qualidade planejada
Formatação/lint (Ruff), checagem de tipos (mypy) e testes (pytest) estão configurados. Dependências estão fixadas no uv.lock. O workflow de CI executa as mesmas verificações; sua execução remota depende do envio ao GitHub. Consulte docs/development.md.

Testes devem cobrir regras e falhas relevantes: precisão monetária, ausências, descontos/taxas suportados, saída inválida, timeout e preservação do histórico. Avaliação probabilística da IA é separada dos testes determinísticos.

## Commits
O usuário fará os commits após revisar cada entrega. Mensagens em inglês, no imperativo, com prefixos docs:, feat:, fix:, test: ou chore:. Não criar commits vazios nem fragmentação artificial para aparentar atividade. Registrar o desenvolvimento real.

## Licenciamento
A licença do código ainda precisa ser escolhida pelo proprietário antes da publicação. Licença e atribuição dos dados são independentes. Não copiar datasets inteiros para o Git por conveniência.
