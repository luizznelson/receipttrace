# ADR-002 — FastAPI e interface sem etapa de build

## Decisão

Servir a API e os arquivos da interface pelo mesmo processo FastAPI. A interface usa HTML semântico, CSS responsivo e módulos JavaScript separados por responsabilidade. Uvicorn executa a aplicação; SQLite continua guardando a revisão.

## Motivo

O produto atual é uma demonstração de três exemplos salvos, com comparação e correção de campos. Essa escolha permite abrir o projeto com um comando Python, reutiliza o domínio existente e evita uma segunda implantação ou configuração de CORS. Não há dependência de CDN, segredo no navegador ou chamada de IA para explorar os exemplos.

Node é usado somente no desenvolvimento: testes nativos, checagem de sintaxe e Prettier, com versão fixada no `package-lock.json`. A aplicação Python não exige instalação npm para funcionar. Um framework pode ser reconsiderado se surgirem rotas e estados que tornem essa estrutura difícil de manter; não foi necessário para o fluxo atual.

## Regras que a API preserva

As ações chamam `ReviewStore`, em vez de reimplementar correção ou conclusão na interface. A versão esperada faz parte do contrato HTTP e conflitos retornam 409. `Decimal` permanece texto no JSON. A extração original e os relatórios publicados não são reescritos pelas ações de revisão.

O catálogo verifica hashes dos arquivos incluídos no pacote. Os indicadores vêm dos relatórios dos 20 documentos; os três exemplos são uma seleção manual para apresentação. As imagens preservam os bytes originais e são distribuídas com atribuição CC BY 4.0.

Os resultados incluídos na aplicação ficam em `webdata/extractions/`, separados das execuções locais de `runs/`. A CI verifica se todos os recursos listados nos checksums estão presentes no wheel, para evitar que regras de exclusão removam dados necessários à demonstração.

## Limites e evolução

O modo público proposto é somente leitura. Revisão mutável é local, com identidade declarada e sem autenticação. Uma aplicação operacional com várias pessoas exigirá identidade, permissões e armazenamento adequado; os controles locais não substituem essas capacidades.

A interface edita cinco campos de totais. Uploads, nova inferência pela web, edição visual de itens e avaliação de produtividade não fazem parte desta entrega. Não houve deploy.

[Guia da aplicação](web.md) · [Arquitetura do domínio](architecture.md)
