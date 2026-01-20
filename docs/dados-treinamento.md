# Dados de treinamento

Os dados de treino ficam em `data/`.

## `data/nlu.yml`

Define exemplos de mensagens para cada intent. O arquivo inclui muitos exemplos de nomes reais para `informar_nome`.
Intents principais:

  - `saudacao`, `menu_inicial`, `sair`.
  - `informar_risco`, `informar_localizacao`, `informar_endereco_texto`.
  - `informar_classificacao_risco`, `informar_descricao_risco`.
  - `pular_descricao_risco`, `pular_enviar_midia_risco`.
  - `corrigir_endereco`, `corrigir_classificacao`, `corrigir_midias`.
  - `contatos_emergencia`, `situacao_no_jacare`.
  - `inatividade_monitoramento`, `inatividade_timeout`.
  - `fallback_texto` (fallback baseado em intent).

Recomendação: mantenha exemplos curtos e representativos. Evite dados pessoais sensíveis.

## `data/stories.yml`

Sequências completas do fluxo de conversa. Cobre:

  - saudação, cadastro de nome e menu inicial;
  - fluxo de informar risco por texto ou localização;
  - correções de endereço, classificação e mídias;
  - comportamento com inatividade.

As stories são essenciais para o aprendizado do TEDPolicy.

## `data/rules.yml`

Regras determinísticas para intents específicos.
Inclui:

  - menu inicial, sair, contatos, situação, etc.;
  - regras para pular descrição e mídias;
  - regras de confirmação de endereço.

## `tests/test_stories.yml`

- Contém cenários de teste para validar diálogos.
- Use esse arquivo como base para novos testes de regressão.

## Dicas para evoluir o treino

- Sempre que adicionar uma nova intent, inclua exemplos em `nlu.yml`.
- Atualize `domain.yml` com intents, entities, slots e actions.
- Se o fluxo mudar, ajuste stories e rules.
- Rode o treinamento para gerar um novo modelo.

[Voltar ao índice](README.md)
