# Banco de dados

## Visão geral

O projeto usa Postgres para:

- tracker store do Rasa (configurado em `endpoints.yml`);
- dados básicos de usuários e mídias (criadas por `migrations.py`).

## Credenciais

As credenciais são lidas de `credentials.yml` pela função `get_db_connection()`.
Em ambiente real, prefira arquivos separados e valores seguros.

## Schema criado por `migrations.py`

### Tabela `usuarios`

Campos:

- `id` (SERIAL, PK)
- `nome` (TEXT)
- `whatsapp_id` (TEXT, UNIQUE)
- `notificacoes` (BOOLEAN)

Usada para:

- salvar o nome do usuário;
- controlar opt-in de notificações.

### Tabela `midias`

Campos:

- `id` (SERIAL, PK)
- `path` (TEXT)
- `mime_type` (TEXT)

Usada para:

- registrar mídias recebidas no WhatsApp.

### Tabela `riscos`

Campos:

- `id`, `timestamp`, `id_usuario`, `latitude`, `longitude`...

Observação: o fluxo atual não grava na tabela `riscos`.
O relato é enviado para o WordPress via API.

### Tabela `pontos_referencia`

Campos:

- `id`, `nome`, `descricao`, `latitude`, `longitude`.

Observação: não há uso ativo dessa tabela nas actions atuais.

## Tracker store do Rasa

Configurado em `endpoints.yml`:

- `type: SQL`
- `dialect: postgresql`
- host: `postgres`
- database: `banco`

Esse tracker store é independente das tabelas criadas por `migrations.py`.

[Voltar ao índice](README.md)
