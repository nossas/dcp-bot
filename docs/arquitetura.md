# Arquitetura e integrações

## Componentes

- Rasa Server: interpreta mensagens, aplica regras/stories e chama actions.
- Action Server: executa lógica customizada, integra com APIs e banco.
- WhatsApp Connector: canal customizado para entrada/saída.
- WordPress: pública e consulta riscos, dicas e informações públicas.
- Google Maps: geocoding de endereços e validação geográfica.
- Postgres: tracker store do Rasa e dados básicos do bot.

## Diagrama de alto nível (texto)

Usuário (WhatsApp)
  -> WhatsApp Cloud API
    -> `whatsapp_connector.WhatsAppInput`
      -> Rasa Server (NLU + Core)
        -> Action Server
           -> WordPress API
           -> Google Maps API
           -> Postgres (usuários/mídias)
        -> Rasa Server
      -> `WhatsAppOutput`
    -> WhatsApp Cloud API
  -> Usuário

## Comunicação entre serviços

- O Rasa Server chama o Action Server via `endpoints.yml`.
- O Action Server consulta WordPress com `WORDPRESS_URL`.
- O Action Server consulta Google Maps com `GOOGLE_MAPS_API_KEY`.
- O Conector do WhatsApp usa `WHATSAPP_AUTH_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`.

## Persistência de dados

- Tracker Store (Rasa): configurado em `endpoints.yml` para Postgres.
- Usuários e mídias: tabelas criadas por `migrations.py`.
- Relatos: enviados ao WordPress, não gravados localmente no fluxo atual.

## Mídias e arquivos

- Mídias recebidas são baixadas no caminho `media/`.
- Em deploy, recomenda-se montar `media/` como volume persistente.

## Limites geográficos

- A validação de endereço restringe a área por um retângulo que limita os endereços ao Jacarezinho.
- Coordenadas do retângulo ficam em `actions/utils.py`.

[Voltar ao índice](README.md)
