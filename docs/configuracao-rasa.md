# Configuração do Rasa

## Arquivo `config.yml`

Define pipeline de NLU e policies de dialogo.

### Pipeline

- `WhitespaceTokenizer`: tokenização simples.
- `RegexFeaturizer`: features baseadas em regex.
- `LexicalSyntacticFeaturizer`: features de contexto.
- `CountVectorsFeaturizer` (char_wb 1-4): n-grams de caracteres.
- `DIETClassifier`: classificador principal (80 epochs).
- `EntitySynonymMapper`: normaliza entidades.
- `ResponseSelector`: selecao de respostas (100 epochs).
- `FallbackClassifier`: fallback quando a confianca e baixa.

### Policies

- `RulePolicy`: aplica regras, fallback e exceptions.
- `MemoizationPolicy`: memoriza conversas (max_history=5).
- `TEDPolicy`: aprendizagem para dialogos (max_history=5).

## Arquivo `domain.yml`

### Intents

Os intents cobrem:
- saudação e navegação (ex.: `saudação`, `menu_inicial`, `sair`);
- informação de risco (ex.: `informar_risco`, `informar_endereço_texto`);
- controle de mídias (ex.: `receber_mídia_risco`, `pular_enviar_mídia_risco`);
- correcoes (ex.: `corrigir_endereço`, `corrigir_classificação`);
- inatividade e fallback (ex.: `inatividade_monitoramento`, `fallback_texto`).

### Slots

- `nome`: nome do usuário (texto).
- `endereço`, `latitude`, `longitude`: localização do risco.
- `classificação_risco`: entidade derivada da escolha do usuário.
- `descrição_risco`: texto livre.
- `mídias`: lista de caminhos de mídia.
- `contexto_classificação_corrigida` e `contexto_endereço_corrigido`: flags de contexto.
- `pagina_risco`: usado para paginação de listagens.

### Responses

Principais respostas estáticas:

- `utter_menu_inicial`
- `utter_classificar_risco`
- `utter_perguntar_por_mídia`
- `utter_finalizar`

## Arquivo `endpoints.yml`

- `action_endpoint`: aponta para `http://action_server:5055/webhook`.
- `tracker_store`: SQL com Postgres (host, porta, usuário e senha).

## Arquivo `credentials.yml`

- Configura o canal customizado `whatsapp_connector.WhatsAppInput`.
- Contem credenciais de WhatsApp e banco.
- Para ambientes reais, prefira usar `credentials-example.yml` e variáveis de ambiente.

[Voltar ao indice](README.md)
