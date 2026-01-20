# Deploy e ambientes

## Dockerfile

Arquivo: `docker/Dockerfile`
- Base: `rasa/rasa:3.2.6`.
- Instala dependências de `requirements.txt`.
- Copia o projeto para `/app`.
- Treina o modelo durante o build (`rasa train`).

## docker-compose.yml (padrão)

- Sobe `bot`, `action_server` e `postgres`.
- Usa volumes para `credentials.yml` e `endpoints.yml`.
- Porta do Rasa: `5005`.
- Porta do Action Server: `5055`.

## docker-compose-local.yml (desenvolvimento)

- Monta o codigo local em `/app`.
- Usa `docker/entrypoint.sh` para aguardar banco e rodar migrations.
- Exige variáveis `POSTGRES_*`, `RASA_URL` e `WORDPRESS_URL`.

Observação: este arquivo contem valores reais de tokens. Substitua por valores seguros.

## docker-compose.deploy.yml (producao)

- Usa imagem pre-buildada `nossas/dcp-bot:latest`.
- Monta `credentials.yml` e `endpoints.yml` externos.
- Monta volume de `media/` para persistência.

## entrypoint.sh

- Aguarda Postgres ficar disponivel.
- Executa `migrations.py` se a tabela `usuários` nao existir.
- Treina o modelo e sobe o Rasa com conector do WhatsApp.

## Variáveis de ambiente

Principais variáveis usadas:
- `WORDPRESS_URL`
- `GOOGLE_MAPS_API_KEY`
- `WHATSAPP_AUTH_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `RASA_URL`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`

[Voltar ao indice](README.md)
