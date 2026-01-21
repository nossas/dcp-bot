# FAQ

## Como alterar um texto do bot?

Depende de onde o texto está definido:

1) Respostas estáticas (respostas `utter_...`)
- Edite `domain.yml` na seção `responses`.
- Exemplo: `utter_menu_inicial`, `utter_perguntar_por_midia`, `utter_finalizar`.

2) Respostas dinâmicas (ações customizadas)
- Edite o texto dentro da action correspondente em `actions/actions.py`.
- Exemplo: mensagens em `action_listar_riscos`, `action_salvar_risco`, `action_preciso_de_ajuda`.

Depois de alterar:
- Se estiver usando Docker, rode novamente `rasa train` ou suba o container com build novo.
- Em desenvolvimento local, reinicie o servidor do Rasa e o action server.

## Como alterar um fluxo do bot?

Um fluxo envolve intents, regras/stories e actions. Passos típicos:

1) Ajuste o comportamento
- Se o fluxo muda a lógica, edite a action em `actions/actions.py`.
- Se for apenas navegação, ajuste as rules em `data/rules.yml` ou stories em `data/stories.yml`.

2) Garanta intents e slots corretos
- Atualize `domain.yml` com intents, slots, actions e responses novas.
- Se houver nova intent, adicione exemplos em `data/nlu.yml`.

3) Treine e valide
- Execute `rasa train`.
- Rode testes de conversa (ex.: `tests/test_stories.yml`) se existirem.

Exemplo simples: mudar o fluxo de "Informar risco" para pedir descrição antes da classificação

- Em `actions/actions.py`, troque a ordem das actions para chamar `action_ask_descricao_risco` antes de `utter_classificar_risco`.
- Em `data/stories.yml` e `data/rules.yml`, reordene os passos do fluxo.
- Em `domain.yml`, confirme intents e slots usados no novo caminho.

## Comportamento inesperado após criar um novo intent, rules ou stories

Verifique nos logs qual o motivo do fluxo não estar seguindo o esperado, caso esteja caindo no fallback adicione mais exemplos no NLU.


[Voltar ao índice](README.md)

