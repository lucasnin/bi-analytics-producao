# Mapeamento do MySQL — pendente

Este arquivo impede que o projeto presuma nomes de tabelas, colunas ou regras do banco real.

Para ativar `DATA_PROVIDER=mysql`, informe:

- tabela/view autorizada de produção e sua granularidade;
- coluna de data de produção;
- valor produzido e valor integrado;
- identificadores e descrições de gerência, equipe, operador, produto, modalidade e convênio;
- coluna/status e quais estados contam em cada métrica;
- fonte e vigência das metas;
- regras de cancelamento, estorno, duplicidade e timezone;
- relacionamentos e filtros de acesso por perfil.

Recomendação: criar views `bi_*` somente leitura e conceder ao usuário da aplicação apenas `SELECT` nessas views.

