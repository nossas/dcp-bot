# Banco de dados

## Visão geral

O projeto usa Postgres para:
- tracker store do Rasa (configurado em `endpoints.yml`);
- dados basicos de usuários e mídias (criadas por `migrations.py`).

## Credenciais

As credenciais sao lidas de `credentials.yml` pela funcao `get_db_connection()`.
Em ambiente real, prefira arquivos separados e valores seguros.

## Schema criado por `migrations.py`

### Tabela `usuários`

Campos:
- `id` (SERIAL, PK)
- `nome` (TEXT)
- `whatsapp_id` (TEXT, UNIQUE)
- `notificações` (BOOLEAN)

Usada para:
- salvar o nome do usuário;
- controlar opt-in de notificações.

### Tabela `mídias`

Campos:
- `id` (SERIAL, PK)
- `path` (TEXT)
- `mime_type` (TEXT)

Usada para:
- registrar mídias recebidas no WhatsApp.

### Tabela `riscos`

Campos:
- `id`, `timestamp`, `id_usuário`, `latitude`, `longitude`...

Observação: o fluxo atual nao grava na tabela `riscos`.
O relato e enviado para o WordPress via API.

### Tabela `pontos_referencia`

Campos:
- `id`, `nome`, `descrição`, `latitude`, `longitude`.

Observação: nao ha uso ativo dessa tabela nas actions atuais.

## Tracker store do Rasa

Configurado em `endpoints.yml`:
- `type: SQL`
- `dialect: postgresql`
- host: `postgres`
- database: `banco`

Esse tracker store e independente das tabelas criadas por `migrations.py`.

[Voltar ao indice](README.md)
