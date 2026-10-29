# Configuração por arquivo — 28/10/2026

Leitura automática de .env local implementada com python-dotenv. Ambiente do processo tem prioridade. Não há busca em pastas superiores, interpolação de valores ou modificação global do ambiente. Mensagens de erro não incluem valores de credenciais.

108 testes passaram, incluindo seis casos isolados com chaves sintéticas para leitura, precedência, UTF-8 BOM, ausência de expansão e isolamento de pastas. Ruff e mypy passaram. .env foi preparado sem ler ou sobrescrever conteúdo existente. Nenhuma chave real foi usada em testes, nenhuma chamada de inferência foi realizada e nenhum commit foi criado.
