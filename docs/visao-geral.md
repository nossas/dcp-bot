# Visão geral

## Objetivo do bot

O chatbot "Defesa Climática Popular" oferece um canal de WhatsApp para:

- registrar relatos de risco (ex.: alagamento, lixo, outros);
- consultar situação recente de riscos na região;
- obter contatos de emergência e dicas de segurança;
- apoiar o usuário com informações e encaminhamentos.

## Canais e integrações principais

- WhatsApp Cloud API (entrada e saída de mensagens);
- Rasa Open Source (NLU + Core);
- Action Server (ações customizadas em Python);
- WordPress (APIs REST para publicar e consultar riscos/dicas);
- Google Maps (geocoding de endereços);
- Postgres (tracker store do Rasa e dados básicos de usuários/mídias).

## Fluxos principais de conversa

1) Saudação e cadastro de nome

- Usuário envia "oi".
- Bot pergunta o nome e salva no banco.
- Exibe o menu inicial.

2) Informar risco (fluxo completo)

- Usuário escolhe "Informar um risco".
- Bot solicita localização ou endereço por texto.
- Bot confirma endereço e pede classificação (alagamento, lixo, outros).
- Bot pede descrição (opcional) e mídias (opcional).
- Bot mostra resumo e pede confirmação.
- Bot envia o relato para o WordPress e encerra o fluxo.

3) Consultar situação no Jacaré

- Usuário escolhe "Situação no Jacaré".
- Bot consulta endpoint de resumo de riscos.
- Bot exibe totais e orienta para o site.

4) Contatos de emergência

- Usuário escolhe "Contatos emergência".
- Bot consulta endpoint de contatos e retorna a lista.

5) Dicas / ajuda

- Bot consulta endpoint de dicas.
- Se não houver retorno, exibe fallback com orientações básicas.

## Controle de inatividade

- O conector do WhatsApp dispara o intent `inatividade_monitoramento`.
- A action agenda um reminder para 5 minutos.
- Se o usuário não responder, o bot envia a mensagem de encerramento.

## Onde encontrar os arquivos

- Ações e utilitários: `actions/actions.py`, `actions/utils.py`, `actions/db_utils.py`
- Conector do WhatsApp: `whatsapp_connector.py`
- Configuração Rasa: `config.yml`, `domain.yml`
- Dados de treino: `data/nlu.yml`, `data/stories.yml`, `data/rules.yml`
- Docker e deploy: `docker/Dockerfile`, `docker/entrypoint.sh`, `docker-compose*.yml`

[Voltar ao índice](README.md)
