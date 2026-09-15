# BI Analytics AI

Plataforma modular de Business Intelligence com dashboard executivo e conversa segura com os dados. A aplicação funciona sem IA e inicia em modo demonstrativo enquanto o esquema real não é fornecido.

## Arquitetura

`Browser → FastAPI route → Service → Semantic rules → Repository → MySQL views`

A IA nunca recebe conexão com o banco nem executa SQL livre. A intenção é classificada em uma lista permitida, o serviço resolve métricas centralizadas e o provedor local apenas explica resultados já calculados. O validador incluído bloqueia mutações e restringe fontes autorizadas caso consultas dinâmicas sejam adicionadas no futuro.

## Tecnologias

Python 3.11+, FastAPI, Pydantic, SQLAlchemy, MySQL/PyMySQL, HTML5, CSS3, JavaScript, ApexCharts, Lucide e Ollama opcional.

## Executar em desenvolvimento

Abra o PowerShell na pasta do projeto e execute:

```powershell
.\setup.ps1
.\start.ps1
```

Os scripts sempre mudam para a pasta correta e executam `uvicorn` pelo ambiente virtual, sem depender de `pip` ou `uvicorn` globais.

Acesse `http://127.0.0.1:8000`. Swagger: `http://127.0.0.1:8000/docs`.

## MySQL

Mantenha `DATA_PROVIDER=demo` até preencher [MYSQL_MAPPING.md](MYSQL_MAPPING.md). Depois implemente o repositório usando views `bi_*`, uma conta somente leitura e parâmetros SQLAlchemy. Configure `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_POOL_SIZE` e `DB_MAX_OVERFLOW` no `.env`. Nunca versione o `.env`.

## Importação CSV

Use `DATA_PROVIDER=csv` para operar com o último arquivo importado. O botão **Importar CSV** valida formato, tamanho e colunas antes de substituir o arquivo ativo. O arquivo fica em `data/imports/current_production.csv` e é carregado uma vez em memória, sendo relido apenas quando muda. A regra temporal replica o Power BI: registros com `Status_Funcao=Integrado` usam `data_integracao`; todos os outros status usam `data_cadastro`. Os valores somam `valor_contrato` e contratos únicos usam `id_front`. `valor_liberacao` permanece disponível para análises futuras, mas não compõe a medida Integrado. `data_atualizacao` informa apenas o horário da última carga. A mesma camada semântica atende KPIs, gráficos, páginas e chat.

## Ollama

Instale o Ollama, execute `ollama pull llama3.1:8b` e confirme que o serviço está em `http://localhost:11434`. Configure `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL` e `OLLAMA_MODEL`. Se estiver offline, respostas determinísticas continuam funcionando normalmente.

## Endpoints principais

- `GET /health`
- `GET /api/dashboard/resumo`
- `GET /api/dashboard/projecao`
- `POST /api/ai/ask`
- `GET /api/imports/production`
- `GET /api/imports/production/filters`
- `POST /api/imports/production`

## Segurança e próximos passos

Há configuração segura, contratos validados, consulta somente leitura por desenho, headers defensivos, IDs de requisição, logs e utilitários JWT/hash. A autenticação não está ligada à UI porque ainda faltam a fonte de usuários e as regras reais de escopo/RLS. Antes de produção: trocar `SECRET_KEY`, cadastrar usuários por um fluxo administrativo, limitar CORS/origens, usar HTTPS, auditar acessos e configurar perfis `ADMIN`, `DIRETORIA`, `GERÊNCIA`, `SUPERVISÃO` e `OPERADOR` segundo o mapeamento real.

### Proteção do banco operacional

A aplicação deve usar uma conta própria com somente `SELECT` e `SHOW VIEW`; nunca reutilize um usuário administrador. O executor de consultas aplica transação read-only, timeout no MySQL, limite de linhas e limite de consultas simultâneas. O pool começa com apenas 3 conexões e 2 excedentes. Dashboards devem usar cache e views analíticas indexadas para evitar consultas repetidas. Ajuste esses limites no `.env` somente depois de medir a carga.

## Testes

```powershell
pytest -q
```

Os testes cobrem projeção por dias úteis, contrato do dashboard, interpretação de intenção e bloqueio de SQL não autorizado.
