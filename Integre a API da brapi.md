Integre a API da brapi.dev neste projeto.

Antes de escrever código:
- Leia https://brapi.dev/llms.txt e https://brapi.dev/openapi.json.
- Se eu não disse qual dado preciso (cotação, histórico, dividendos, balanços, FIIs, câmbio ou macro), pergunte antes.
- Escolha uma operação /api/v2 específica. Use o parâmetro symbols para buscar vários ativos em uma chamada.

Ao implementar:
- Leia a chave da variável de ambiente BRAPI_TOKEN. Não coloque a chave no código, no frontend ou no repositório.
- Envie a chave no header Authorization: Bearer <BRAPI_TOKEN>.
- Trate 401, 404, 429 (respeite Retry-After) e campos null.
- Use o cliente HTTP e os padrões que o projeto já usa.
- Teste com PETR4 e VALE3 e me mostre a resposta.

Para dúvidas sobre um campo, consulte https://brapi.dev/api/v2/dictionary.