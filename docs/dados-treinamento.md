# Dados de treinamento

Os dados de treino ficam em `data/`.

## `data/nlu.yml`

- Define exemplos de mensagens para cada intent.
- O arquivo inclui muitos exemplos de nomes reais para `informar_nome`.
- Intents principais:
  - `saudação`, `menu_inicial`, `sair`.
  - `informar_risco`, `informar_localização`, `informar_endereço_texto`.
  - `informar_classificação_risco`, `informar_descrição_risco`.
  - `pular_descrição_risco`, `pular_enviar_mídia_risco`.
  - `corrigir_endereço`, `corrigir_classificação`, `corrigir_mídias`.
  - `contatos_emergência`, `situação_no_jacare`.
  - `inatividade_monitoramento`, `inatividade_timeout`.
  - `fallback_texto` (fallback baseado em intent).

Recomendação: mantenha exemplos curtos e representativos. Evite dados pessoais sensiveis.

## `data/stories.yml`

- Sequencias completas do fluxo de conversa.
- Cobre:
  - saudação, cadastro de nome e menu inicial;
  - fluxo de informar risco por texto ou localização;
  - correcoes de endereço, classificação e mídias;
  - comportamento com inatividade.

As stories sao essenciais para o aprendizado do TEDPolicy.

## `data/rules.yml`

- Regras deterministicas para intents especificos.
- Inclui:
  - menu inicial, sair, contatos, situação, etc.;
  - regras para pular descrição e mídias;
  - regras de confirmação de endereço.

## `tests/test_stories.yml`

- Contem cenarios de teste para validar dialogos.
- Use esse arquivo como base para novos testes de regressao.

## Dicas para evoluir o treino

- Sempre que adicionar uma nova intent, inclua exemplos em `nlu.yml`.
- Atualize `domain.yml` com intents, entities, slots e actions.
- Se o fluxo mudar, ajuste stories e rules.
- Rode o treinamento para gerar um novo modelo.

[Voltar ao indice](README.md)
