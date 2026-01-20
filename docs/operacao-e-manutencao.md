# Operação e manutenção

## Treinamento do modelo

- O treinamento e executado no build do Dockerfile e no `entrypoint.sh`.
- Para treinar manualmente:

```
rasa train
```

O modelo gerado fica em `models/`.

## Logs

- Rasa e actions registram logs no console.
- Existem arquivos de log no repo (`log.log`, `log-actions.log`, etc.).
- Em producao, prefira coletar logs via stdout/stack do container.

## Mídias recebidas

- Mídias sao baixadas para `media/`.
- Em deploy, monte `media/` como volume persistente.

## Inatividade

- O conector dispara `inatividade_monitoramento`.
- A action agenda um reminder de 5 minutos.
- Em caso de timeout, o bot envia mensagem de encerramento.

## Manutenção de dados

- Se for necessario resetar cadastro local, limpe as tabelas em Postgres.
- `migrations.py` recria as tabelas básicas, mas nao apaga dados.

## Segurança e segredos

- Evite commitar tokens e chaves em `credentials.yml`.
- Use `credentials-example.yml` e variáveis de ambiente.
- Restrinja o acesso ao volume de `media/`.

## Healthcheck

- O conector expõe `GET /` para healthcheck simples.
- A rota `GET /webhook` valida o token do WhatsApp.

[Voltar ao indice](README.md)
