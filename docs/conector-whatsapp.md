# Conector do WhatsApp

O conector customizado esta em `whatsapp_connector.py`..

## Componentes principais

- `WhatsAppInput` (InputChannel)
  - Recebe mensagens do webhook.
  - Interpreta mensagens de texto, botoes, localização e mídias.

- `WhatsAppOutput` (OutputChannel)
  - Envia mensagens de texto, botoes e mídias.
  - Implementa envio de payloads customizados.

## Rotas HTTP

O `WhatsAppInput.blueprint()` registra as rotas:
- `GET /` healthcheck simples.
- `GET /webhook` validação do token.
- `POST /webhook` processamento das mensagens.

## Fluxo de entrada de mensagens

1) Webhook recebe payload do WhatsApp.

2) O conector identifica o tipo de mensagem.

3) Para texto/botoes: envia para `on_new_message`.

4) Para localização: serializa como JSON string e envia ao Rasa.

5) Para mídias (imagem/video): baixa o arquivo e agrega em lote.

## Tratamento de mídias

- Mídias sao baixadas via `heyoo` e salvas em `media/`.
- O conector agrupa mídias enviadas em sequencia.
- O payload final possui o formato:

```json
{"tipo": "midia_combinada", "midias": [{"mime_type": "...", "path": "..."}]}
```

Esse payload e consumido por `action_salvar_mídia_risco`.

## Indicador de digitando

- `send_typing()` envia um payload para marcar como lido e exibir digitação.
- Usado antes de respostas demoradas e processamento de mídias.

## Payloads customizados

O `WhatsAppOutput.send_custom_json()` aceita:

- `{"type": "location_request"}`: solicita localização.
- `{"type": "media_id"}`: envia mídia ja cadastrada no WhatsApp.
- `{"type": "video"}`: envia video por URL.

## Inatividade

A funcao `agendar_inatividade()` chama o endpoint do Rasa:
- `POST /conversations/<sender_id>/trigger_intent`
- intent: `inatividade_monitoramento`

Isso aciona a action que agenda o reminder.

## Credenciais e variáveis

- `credentials.yml` define `auth_token`, `phone_number_id`, `verify_token`.
- Variáveis de ambiente usadas:
  - `WHATSAPP_AUTH_TOKEN`
  - `WHATSAPP_PHONE_NUMBER_ID`
  - `RASA_URL`


[Voltar ao indice](README.md)
