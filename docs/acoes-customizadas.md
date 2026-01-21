# Ações customizadas

As actions estão em `actions/actions.py`. Funções auxiliares estão em `actions/utils.py` e `actions/db_utils.py`.

## Visão geral

As actions implementam:

- cadastro e persistência de usuário;
- coleta de localização e validação geográfica;
- registro e confirmação de relato de risco;
- consulta a informações públicas (riscos, abrigos, contatos, dicas);
- controle de inatividade e encerramento de conversa.

## Fallback e inatividade

- `action_fallback_buttons`
  - Decide a melhor ação quando o NLU cai em fallback.
  - Considera a última action e oferece botões de retomada.

- `action_agendar_inatividade`
  - Agenda um reminder para 5 minutos.
  - Usado quando o usuário fica sem responder.

- `action_inatividade_timeout`
  - Envia mensagem de encerramento.
  - Reseta slots ligados ao relato em andamento.

## Cadastro e identidade do usuário

- `action_perguntar_nome`
  - Busca nome no banco por `whatsapp_id`.
  - Se existir, carrega no slot e abre menu.
  - Caso contrário, pergunta como o usuário prefere ser chamado.

- `action_salvar_nome`
  - Salva ou atualiza o nome em `usuarios`.
  - Define o slot `nome` e retorna para o menu.

- `action_corrigir_nome`
  - Remove nome do banco e do slot.
  - Pergunta novamente o nome.

- `action_alterar_nome`
  - Pergunta se deseja corrigir ou manter o nome.

- `action_repeat_last_message`
  - Reenvia a última mensagem do bot (regra "tentar novamente").

## Localização e endereço

- `action_request_location`
  - Solicita localização via WhatsApp ou endereço em texto.
  - Reseta slots `endereco`, `latitude` e `longitude`.

- `action_buscar_endereco`
  - Recebe JSON de localização e tenta obter endereço.
  - Valida se a coordenada está dentro do retângulo definido.
  - Confirma endereço com botões `affirm_address` / `deny_address`.

- `action_buscar_endereco_texto`
  - Faz geocoding com o texto do usuário.
  - Confirma endereço e seta slots de latitude/longitude.

## Classificação, descrição e mídias

- `action_salvar_classificacao_risco`
  - Usa o slot `classificacao_risco` vindo da entidade.
  - Encaminha para coleta de descrição.

- `action_ask_descricao_risco`
  - Solicita descrição textual (opcional) e oferece "pular".

- `action_salvar_descricao_risco`
  - Confirma descrição e avança para mídias ou confirmação.

- `action_salvar_midia_risco`
  - Recebe JSON com mídias enviadas pelo conector.
  - Armazena caminhos no slot `midias`.

- `action_perguntar_por_nova_midia`
  - Pergunta se o usuário deseja enviar mais mídias.

## Confirmação e ajustes do relato

- `action_confirmar_relato`
  - Mostra resumo (endereço, tipo, descrição) e mídias.

- `action_confirmar_relato_pos_midia`
  - Solicita confirmação final do relato.

- `action_recusar_risco`
  - Pergunta o que deseja corrigir (endereço, classificação, mídias).

- `action_corrigir_midias`
  - Limpa `midias` e retorna ao envio.

- `action_classificar_risco_corrigir`
  - Reabre a classificação com contexto de correção.

- `action_corrigir_endereco`
  - Marca contexto de correção de endereço e reabre localização.

## Salvamento do relato

- `action_salvar_risco`
  - Garante usuário em `usuarios`.
  - Insere mídias em `midias` (se houver).
  - Envia o relato para o WordPress via `enviar_risco_para_wordpress`.
  - Reseta os slots do relato.

Observação: a tabela `riscos` existe no schema, mas o fluxo atual não insere dados nela.

## Consultas e informações

- `action_listar_riscos`
  - Consulta resumo das últimas 24h em `wp-json/dcp/v1/riscos-resumo`.

- `action_nivel_de_risco`
  - Consulta nível de risco em `wp-json/dcp/v1/risco-regiao`.

- `action_preciso_de_ajuda`
  - Consulta dicas em `wp-json/dcp/v1/dicas?active=1`.
  - Se falhar, usa texto fallback.

- `action_listar_abrigos`
  - Consulta lista de abrigos em `wp-json/dcp/v1/abrigos`.

- `action_listar_contatos_emergencia`
  - Consulta contatos em `wp-json/dcp/v1/contatos`.

## Notificações

- `action_pergunta_notificacoes`
  - Verifica status de notificações do usuário.

- `action_receber_notificacoes`
  - Marca `usuarios.notificacoes = TRUE`.

- `action_parar_notificacoes`
  - Marca `usuarios.notificacoes = FALSE`.

## Encerramento

- `action_sair`
  - Envia mensagem de despedida e reseta slots.

- `action_agradecimento`
  - Envia resposta curta e agenda fim da conversa.

## Utilitários (`actions/utils.py`)

- `get_last_action`, `get_last_intent`: navega no tracker.
- `extrair_riscos`: normaliza lista de riscos de um JSON.
- `verificar_tipo_arquivo`: detecta tipo de mídia pelo MIME.
- `enviar_risco_para_wordpress`: POST com dados e mídias.
- `formata_data`: formatação de data ISO.
- `dentro_do_retangulo`: valida área geográfica.
- `verifica_poligono`: filtra resultados do Google Maps.
- `chamada_google_maps`: geocoding com limites de area.
- `format_address`: normaliza endereço.
- `get_endereco_latlong` / `get_endereco_texto`: helpers de geocoding.

## Banco (`actions/db_utils.py`)

- `load_db_credentials`: lê credenciais do banco em `credentials.yml`.
- `get_db_connection`: abre conexão com Postgres.

[Voltar ao índice](README.md)
