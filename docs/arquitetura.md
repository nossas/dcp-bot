# Arquitetura e integrações

## Componentes

- Rasa Server: interpreta mensagens, aplica regras/stories e chama actions.
- Action Server: executa logica customizada, integra com APIs e banco.
- WhatsApp Connector: canal customizado para entrada/saida.
- WordPress: pública e consulta riscos, dicas e informações públicas.
- Google Maps: geocoding de endereços e validação geografica.
- Postgres: tracker store do Rasa e dados basicos do bot.

## Diagrama de alto nivel (texto)

Usuario (WhatsApp)
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
  -> Usuario

## Comunicação entre serviços

- O Rasa Server chama o Action Server via `endpoints.yml`.
- O Action Server consulta WordPress com `WORDPRESS_URL`.
- O Action Server consulta Google Maps com `GOOGLE_MAPS_API_KEY`.
- O Conector do WhatsApp usa `WHATSAPP_AUTH_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`.

## Persistência de dados

- Tracker Store (Rasa): configurado em `endpoints.yml` para Postgres.
- Usuarios e mídias: tabelas criadas por `migrations.py`.
- Relatos: enviados ao WordPress, nao gravados localmente no fluxo atual.

## Media e arquivos

- Mídias recebidas sao baixadas no caminho `media/`.
- Em deploy, recomenda-se montar `media/` como volume persistente.

## Limites geograficos

- A validação de endereço restringe a área por um retângulo que limita os endereços ao Jacarezinho.
- Coordenadas do retângulo ficam em `actions/utils.py`.

[Voltar ao indice](README.md)
