from rasa_sdk import Action
from rasa_sdk.events import UserUtteranceReverted, SlotSet
import requests
import json
import logging
from rasa_sdk.events import FollowupAction, ReminderScheduled, AllSlotsReset, ReminderCancelled, Restarted
from rasa_sdk.executor import CollectingDispatcher
from .db_utils import get_db_connection
import os
from datetime import datetime, timedelta,timezone
import time
import sys
from whatsapp_connector import WhatsAppOutput
import pytz
from typing import Any, Text, Dict, List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
logging.basicConfig(level=logging.DEBUG)  # Força o nível global de debug
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 
from .utils import *
import re
        
class ActionFallbackButtons(Action):
    def name(self):
        return "action_fallback_buttons"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_fallback_buttons")
        logger.debug("Fallback!")
        last_action = None
        last_action = get_last_action(tracker)
        user_message = tracker.latest_message.get("text")
        if 'sair' in  user_message.lower():
            return [
                FollowupAction("action_sair")
            ]
        if 'menu inicial' in  user_message.lower():
            return [
                FollowupAction("utter_menu_inicial")
            ]
        if last_action == "action_perguntar_nome" or last_action == "action_corrigir_nome":
            logger.debug(f"Salvando fallback como nome: {user_message}")
            return [
                FollowupAction("action_salvar_nome")
            ]

        nome = tracker.get_slot("nome")
        if not nome:
            return [FollowupAction("action_perguntar_nome")]

        # Verifica se a última ação foi action_ask_descricao_risco
        if last_action == "action_ask_descricao_risco":
            user_message = tracker.latest_message.get("text")
            logger.debug(f"Salvando fallback como descrição de risco: {user_message}")
            correcao_classificacao = tracker.get_slot("contexto_classificacao_corrigida")
            next_action = "utter_perguntar_por_midia" if not correcao_classificacao else "action_confirmar_relato"
            return [
                SlotSet("descricao_risco", user_message),
                FollowupAction(next_action)
            ]
        if last_action == "action_request_location":
            logger.debug(f"Fallback de localização")
            return [
                FollowupAction("action_buscar_endereco_texto")
            ]
        if last_action == "utter_menu_inicial":
            logger.debug(f"Fallback de menu inicial")
            return [
                FollowupAction("utter_menu_inicial")
            ]
        if last_action == "action_buscar_endereco_texto":
            logger.debug(f"Fallback de buscar endereço")
            logger.debug(f"user_message: {user_message}")
            dispatcher.utter_message(text="Não consegui entender esse endereço.\nVocê pode tentar de novo.")
            return [
                    FollowupAction("action_request_location")
            ]
        # Caso contrário, volta ao fallback padrão
        last_bot_message = None
        for event in reversed(tracker.events):
            if event.get("event") == "bot":
                last_bot_message = event.get("text")
                break

        buttons = [
            {"title": "Menu inicial", "payload": "/menu_inicial"},
            {"title": "Tentar novamente", "payload": "/tentar_novamente"}
        ]

        dispatcher.utter_message(text="Desculpe, não consegui entender.\nVocê pode continuar escolhendo uma das opções abaixo:", buttons=buttons)
        return [UserUtteranceReverted()]


class ActionAgendarInatividade(Action):
    def name(self):
        return "action_agendar_inatividade"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_agendar_inatividade")
        trigger_date_time = datetime.now(pytz.timezone("America/Sao_Paulo")) + timedelta(minutes=3)
        logger.debug(f"agendando timeout para: {trigger_date_time}")
        
        return [
            ReminderScheduled(
                "inatividade_timeout",
                trigger_date_time = trigger_date_time,
                name="lembrete_inatividade",
                kill_on_user_message=True
            ),
            FollowupAction("action_listen")
        ]

        
class ActionInatividadeTimeout(Action):
    def name(self) -> Text:
        return "action_inatividade_timeout"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_inatividade_timeout")
        recipient_id = tracker.sender_id
        message = "Percebi que você não respondeu. Vou encerrar a conversa, mas se quiser falar comigo novamente, é só mandar um ‘oi’. 👋🏽"
        last_action = get_last_action(tracker)
        if last_action == 'action_sair':
            return[]
        # Forçar envio direto usando a API do WhatsApp
        output_channel = WhatsAppOutput(auth_token=os.getenv("WHATSAPP_AUTH_TOKEN"),phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"))
        logger.debug(os.getenv("WHATSAPP_AUTH_TOKEN"))

        output_channel.send_message(message, recipient_id)

        # Para compatibilidade com o tracker
        dispatcher.utter_message(text=message)
        
        return [
            SlotSet("classificacao_risco", None),
            SlotSet("descricao_risco", None),
            SlotSet("endereco", None),
            SlotSet("latitude", None),
            SlotSet("longitude", None),
            SlotSet("midias", []),
            SlotSet("contexto_endereco_corrigido", False), 
            SlotSet("contexto_classificacao_corrigida", False)
        ]


class ActionRequestLocation(Action):
    def name(self):
        return "action_request_location"

    def run(self, dispatcher, tracker, domain): 
        logger.debug("rodando action: action_request_location")
        
        latitude = tracker.get_slot("latitude")
        longitude = tracker.get_slot("longitude")
        endereco = tracker.get_slot("endereco")
        nome = tracker.get_slot("nome")
        classificacao_risco = tracker.get_slot("classificacao_risco")
        logger.debug(f"solicitando localização")
        dispatcher.utter_message(text="Precisamos saber onde está o risco que você quer compartilhar. Você pode:")
        dispatcher.utter_message(text="✏️ *Digitar o endereço:* Como por exemplo 'Rua Senador Nabuco, 11, Jacarezinho'")
        dispatcher.utter_message(text="📍 *Enviar sua localização atual:* Se clicar no botão abaixo o WhatsApp vai pedir permissão para usar sua localização - é só aceitar.",custom={"type": "location_request"})
        return [
            SlotSet("endereco", None),
            SlotSet("latitude", None),
            SlotSet("longitude", None),
            FollowupAction("action_listen")
            ]

class ActionAlterarNome(Action):
    def name(self):
        return "action_alterar_nome"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_alterar_nome")
        dispatcher.utter_message(
                text="Entendi, você quer corrigir o nome que foi informado, certo?",
                buttons=[
                    {"title": "Corrigir nome", "payload": "/corrigir_nome"},
                    {"title": "Manter como está", "payload": "/menu_inicial"}
                ]
            )
        return[]

class ActionRepeatLastMessage(Action):
    def name(self):
        return "action_repeat_last_message"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_repeat_last_message")
        last_bot_messages = []
        last_action = None
        last_action = get_last_action(tracker)
        
        # for event in reversed(tracker.events):
        #     if event.get("event") == "bot":
        #         last_bot_messages.append(event.get("text"))
        #         if len(last_bot_messages) == 2:
        #             break

        # if len(last_bot_messages) == 2:
        #     penultima_mensagem = last_bot_messages[1]
        #     dispatcher.utter_message(text=penultima_mensagem)
        if last_action:
            dispatcher.utter_message("Vamos tentar de novo.")
            return [FollowupAction(last_action)]
        else:
            dispatcher.utter_message(text="Desculpe, não consigo repetir a última mensagem.")
            return [FollowupAction("utter_menu_inicial")]
    
class ActionPerguntarNome(Action):
    def name(self):
        return "action_perguntar_nome"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_perguntar_nome")
        sender_id = tracker.sender_id
       
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT nome FROM usuarios 
                    WHERE whatsapp_id = %s AND nome IS NOT NULL
                """, (sender_id,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()

                if row:
                    nome = row[0]
                    logger.debug(f"Nome encontrado no banco: {nome}")
                    return [SlotSet("nome", nome),SlotSet("pagina_risco",1),FollowupAction("utter_menu_inicial")]

        except Exception as e:
            logger.error(f"Erro ao buscar nome no banco: {e}")

        dispatcher.utter_message(
            text="Oie! Bem-vindo(a) à Defesa Climática Popular.\nPra começar, *como você prefere ser chamado(a)?*"
        )
        
        return [SlotSet("pagina_risco",1)]

class ActionSalvarNome(Action):
    def name(self):
        return "action_salvar_nome"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_salvar_nome")
        last_action = get_last_action(tracker)
        if last_action == 'action_request_location':
            return [FollowupAction("action_buscar_endereco_texto")]

        nome = tracker.latest_message.get("text") if tracker.latest_message.get("text") != '/affirm_name' else tracker.get_slot("nome")
        nome = nome.title()
        whatsapp_id = tracker.sender_id
        logger.debug(f"Buscando id do wa")
        if nome:
            try:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO usuarios (nome,whatsapp_id)
                        VALUES (%s, %s)
                        ON CONFLICT (whatsapp_id) DO UPDATE SET nome = EXCLUDED.nome
                    """, (nome,whatsapp_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return[FollowupAction("action_perguntar_nome")]
                else:
                    dispatcher.utter_message(text="Erro ao conectar ao banco de dados.")
            except Exception as e:
                dispatcher.utter_message(text="Ocorreu um erro ao salvar seu nome.")
                print(f"[ERRO BANCO] {e}")
        else:
            dispatcher.utter_message(text="Não consegui entender seu nome.")
        logger.debug(f"Salvando nome no slot e n")
        return [SlotSet("nome", nome),FollowupAction("action_perguntar_nome")]

class ActionApagarNome(Action):
    def name(self):
        return "action_corrigir_nome"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_corrigir_nome")
        logger.debug("Apagando nome do slot e do banco.")

        whatsapp_id = tracker.sender_id

        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET nome = NULL WHERE whatsapp_id = %s;",
                    (whatsapp_id,)
                )
                conn.commit()
                logger.debug(f"Nome apagado do banco para {whatsapp_id}")
        except Exception as e:
            logger.error(f"Erro ao apagar nome do banco: {e}")
            dispatcher.utter_message(text="Ocorreu um erro ao apagar seu nome do sistema.")
        finally:
            if conn:
                conn.close()
        dispatcher.utter_message(text="Sem problemas! Como você prefere ser chamado(a)?")
        return [SlotSet("nome", None)]    
class ActionBuscarEndereco(Action):
    def name(self):
        return "action_buscar_endereco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_buscar_endereco")
        user_message = tracker.latest_message.get("text")
        logger.debug(f"entrou na action user_message: {user_message}")
        
        try:
            location_data = json.loads(user_message)
            latitude = location_data["latitude"]
            longitude = location_data["longitude"]
            if not location_data.get('address'):
                logger.debug(f"latitude: {latitude}")
                logger.debug(f"longitude: {longitude}")
                logger.debug(f"não tem endereço")
                endereco = get_endereco_latlong(latitude,longitude )
                if endereco:
                    dispatcher.utter_message(
                        text=f"Encontrei esse endereço:\n{endereco}\nEstá correto?",
                        buttons=[
                            {"title": "Sim", "payload": "/affirm_address"},
                            {"title": "Não", "payload": "/deny_address"}
                        ]
                    )
                    logger.debug(f"achou endereço: {endereco}")
                    
                    return [
                        SlotSet("latitude", latitude),
                        SlotSet("longitude", longitude),
                        SlotSet("endereco", endereco),
                        FollowupAction("action_listen")
                    ]
                else:
                    dispatcher.utter_message(text="Não consegui encontrar esse lugar.\nVocê pode tentar de novo.")
                    return [FollowupAction("action_request_location")]
            else:
                logger.debug(f"tem endereço")
                endereco = location_data['address']
                dispatcher.utter_message(
                    text=f"Encontrei esse endereço:\n{endereco}\nEstá correto?",
                    buttons=[
                        {"title": "Sim", "payload": "/affirm_address"},
                        {"title": "Não", "payload": "/deny_address"}
                    ]
                )
                return [
                    SlotSet("latitude", latitude), 
                    SlotSet("longitude", longitude), 
                    SlotSet("endereco", endereco),
                    FollowupAction("action_listen")
                    ]
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Erro ao processar JSON ou chave não encontrada: {e}")
            dispatcher.utter_message(
                text=f"Acho que a sua localização não veio de forma correta, você quer enviar um endereço?",
                buttons=[
                    {"title": "Sim", "payload": "/sim"},
                    {"title": "Não", "payload": "/nao"}
                ]
            )
            return []

class ActionBuscarEnderecoTexto(Action):
    def name(self):
        return "action_buscar_endereco_texto"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_buscar_endereco_texto")
        logger.debug(f"ultima mensagem: {tracker.latest_message}")
        last_action = None
        last_action = get_last_action(tracker)
        if last_action == "action_perguntar_nome" or last_action == "action_corrigir_nome":
            user_message = tracker.latest_message.get("text")
            logger.debug(f"Salvando fallback como nome: {user_message}")
            return [
                FollowupAction("action_salvar_nome")
            ]
        endereco_texto = tracker.latest_message.get("text")   
        coords = get_endereco_texto(endereco_texto)
        logger.debug(coords)
        if coords:
            endereco = coords.get("endereco", "Endereço não encontrado.")
            latitude = coords.get("lat","")
            longitude = coords.get("lng","")
            dispatcher.utter_message(
                text=f"Encontrei esse endereço:\n{endereco}\nEstá correto?",
                buttons=[
                    {"title": "Sim", "payload": "/affirm_address"},
                    {"title": "Não", "payload": "/deny_address"}
                ]
            )
            return [
                SlotSet("latitude", latitude),
                SlotSet("longitude", longitude),
                SlotSet("endereco", endereco),
                FollowupAction("action_listen")

            ]
        else:
            logger.debug(f"Não encontrou endereço: {endereco}")
            dispatcher.utter_message(text="Não consegui encontrar esse lugar.\nVocê pode tentar de novo.")
        return [FollowupAction("action_request_location")]

class ActionSalvarClassificacaoRisco(Action):
    def name(self) -> str:
        return "action_salvar_classificacao_risco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_salvar_classificacao_risco")
        last_action = get_last_action(tracker)
        risco = tracker.get_slot("classificacao_risco")
        logger.debug(risco)
        next_action = "action_ask_descricao_risco"
        if risco:
            return [
                SlotSet("classificacao_risco", risco),
                FollowupAction(next_action)
            ]        
        else:
            dispatcher.utter_message(text="Não consegui entender a classificação do risco.")
            return [FollowupAction(last_action)]

class ActionSolicitarDescricaoRisco(Action):
    def name(self) -> str:
        return "action_ask_descricao_risco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_ask_descricao_risco")
        
        last_action = get_last_action(tracker,2)
        risco = tracker.get_slot("classificacao_risco")
        action_classificar = "utter_classificar_risco" if last_action == "utter_classificar_risco" else "action_classificar_risco_corrigir"
        if risco:
            dispatcher.utter_message(
                text=f"Se puder, conte um pouco mais sobre o que está acontecendo. Isso ajuda a entender melhor a situação.",
            )
            dispatcher.utter_message(
                text=f"Você pode *escrever uma mensagem* ou clicar em *pular* para continuar.",
                buttons=[
                    {"title": "Pular", "payload": "/pular_descricao_risco"},
                ]
            )
            return [SlotSet("descricao_risco", None),FollowupAction('action_listen')]        
        else:
            dispatcher.utter_message(text="Não consegui entender a classificação do risco.")
            return [FollowupAction(action_classificar)]

class ActionSalvarDescricaoRisco(Action):
    def name(self) -> str:
        return "action_salvar_descricao_risco"
    
    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_salvar_descricao_risco")
        last_action = get_last_action(tracker,3)
        next_action = "utter_perguntar_por_midia" if last_action == "utter_classificar_risco" else "action_confirmar_relato"
        descricao = tracker.get_slot("descricao_risco")
        if descricao:
            dispatcher.utter_message(text="Obrigado pela descrição!")
            return [FollowupAction(next_action)]
        else:
            dispatcher.utter_message(text="Não consegui entender a descrição, tente novamente.")
            return [FollowupAction("action_ask_descricao_risco")]

class ActionSalvarMidiaRisco(Action):
    def name(self) -> str:
        return "action_salvar_midia_risco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_salvar_midia_risco")
        try:
            user_message = tracker.latest_message.get("text")
            midia_data = json.loads(user_message)

            midias_slot = tracker.get_slot("midias") or []
            logger.debug(f"midia_data: {midia_data}")

            if midia_data.get("tipo") == "mídia_combinada":
                novas_midias = [m["path"] for m in midia_data["midias"]]
                midias_slot.extend(novas_midias)
                dispatcher.utter_message(text=f"Estou recebendo. Se ainda tiver arquivos carregando, aguarde concluir.")
            else:
                # Caso venha uma mídia só
                path = midia_data["path"]
                midias_slot.append(path)
                dispatcher.utter_message(text="Foto/vídeo adicionado!")

            return [SlotSet("midias", midias_slot)]

        except Exception as e:
            dispatcher.utter_message(
                text="*Opa, algo deu errado com o envio.*\nVocê pode tentar de novo ou pular essa parte, como preferir.", 
                buttons=[
                    {"title": "Não enviar", "payload": "/pular_enviar_midia_risco"},
                ])
            logger.error(f"Erro ao salvar mídia no slot: {e}")
            return []

class ActionConfirmarRisco(Action):
    def name(self) -> str:
        return "action_confirmar_relato"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_confirmar_relato")
        
        endereco = tracker.get_slot("endereco") or "não informado"
        classificacao = tracker.get_slot("classificacao_risco") or "não informado"
        descricao = tracker.get_slot("descricao_risco") or "não informado"
        midias_slot = tracker.get_slot("midias") or []
        
        mensagem = (
            f"Resumo do seu relato:\n"
            f"📍 *Endereço:* {endereco}\n"
            f"⚠️ *Tipo de risco:* {classificacao}\n"
            f"📝 *Descrição:* {descricao}\n\n"
        )
        dispatcher.utter_message(text=mensagem)
        if (len(midias_slot)):
            dispatcher.utter_message(text="📸 Fotos/vídeos: ")
            for midia in midias_slot:
                media_type = verificar_tipo_arquivo(midia)
                media_path = os.path.splitext(midia)[0]
                media_id = os.path.basename(media_path)
                dispatcher.utter_message(text="", custom={"type": "media_id", "media_id": media_id, "media_type":media_type})   
        return [
           FollowupAction("action_confirmar_relato_pos_midia")
           ]

class ActionConfirmarRiscoPosMidia(Action):
    def name(self) -> str:
        return "action_confirmar_relato_pos_midia"

    def run(self, dispatcher, tracker, domain):
        time.sleep(3)
        logger.debug("rodando action: action_confirmar_relato_pos_midia")
        dispatcher.utter_message(text="Essas informações estão corretas? Se sim, clique em *Confirmar e enviar*.")
        dispatcher.utter_message(text="Seu relato será salvo com segurança, passará por uma verificação rápida e, se aprovado, será publicado no mapa. Tudo conforme nossa política de privacidade (saiba mais em bit.ly/termo-privacidade)")
        mensagem = ("Confirmar envio:")
        dispatcher.utter_message(
            text=mensagem,
            buttons=[
                {"title": "Confirmar e enviar", "payload": "/afirmar_confirmacao_risco"},
                {"title": "Corrigir informações", "payload": "/recusar_confirmacao_risco"}
            ]
        )

        return [
            SlotSet("contexto_classificacao_corrigida", False), 
                SlotSet("contexto_endereco_corrigido", False)]

class ActionRecusarRisco(Action):
    def name(self) -> str:
        return "action_recusar_risco"
    
    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_recusar_risco")
        dispatcher.utter_message(
            text="Qual informação deseja atualizar?",
            buttons=[
                {"title": "Endereço", "payload": "/corrigir_endereco"},
                {"title": "Tipo/Descrição", "payload": "/corrigir_classificacao"},
                {"title": "Imagens/Vídeos", "payload": "/corrigir_midias"}
            ]
        )
        return []

class ActionCorrigirMidias(Action):
    def name(self) -> str:
        return "action_corrigir_midias"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_corrigir_midias")
        return [
            SlotSet("midias", []),
            FollowupAction("utter_perguntar_por_midia")
        ]

class ActionClassificarRiscoCorrigir(Action):
    def name(self):
        return "action_classificar_risco_corrigir"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_classificar_risco_corrigir")
        nome = tracker.get_slot("nome") or ""
        dispatcher.utter_message(
            text=f"Perfeito {nome}. Você quer falar sobre:",
            buttons=[
                {"title": "Alagamento", "payload": '/informar_classificacao_risco{"classificacao_risco": "alagamento"}'},
                {"title": "Lixo", "payload": '/informar_classificacao_risco{"classificacao_risco": "lixo"}'},
                {"title": "Outros", "payload": '/informar_classificacao_risco{"classificacao_risco": "outros"}'}
            ]
        )
        return [SlotSet("contexto_classificacao_corrigida", True), FollowupAction("action_listen")]

class ActionEnderecoRiscoCorrigir(Action):
    def name(self):
        return "action_corrigir_endereco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_corrigir_endereco")
        return [SlotSet("contexto_endereco_corrigido", True), FollowupAction("action_request_location")]
    
class ActionSalvarRisco(Action):
    def name(self) -> str:
        return "action_salvar_risco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_salvar_risco")
        try:
            conn = get_db_connection()
            if not conn:
                dispatcher.utter_message(text="Erro ao conectar ao banco de dados.")
                return []

            cursor = conn.cursor()
            nome = tracker.get_slot("nome")
            endereco = tracker.get_slot("endereco")
            classificacao = tracker.get_slot("classificacao_risco")
            descricao = tracker.get_slot("descricao_risco")
            latitude = tracker.get_slot("latitude")
            longitude = tracker.get_slot("longitude")
            midias = tracker.get_slot("midias") or []
            whatsapp_id = tracker.sender_id

            # Buscar ou criar usuário
            cursor.execute("SELECT id FROM usuarios WHERE whatsapp_id = %s", (whatsapp_id,))
            usuario = cursor.fetchone()

            if usuario:
                usuario_id = usuario[0]
            else:
                cursor.execute("INSERT INTO usuarios (whatsapp_id, nome) VALUES (%s, %s) RETURNING id", (whatsapp_id, nome))
                usuario_id = cursor.fetchone()[0]

            # Inserir mídias e coletar ids
            id_midias = []
            logger.debug(f"midias a salvar: {midias}")
            for midia_path in midias:
                # Aqui mime_type é opcional — você pode adaptar para pegar do nome do arquivo ou outro slot
                cursor.execute("""
                    INSERT INTO midias (path, mime_type)
                    VALUES (%s, %s) RETURNING id
                """, (midia_path, None))  # ou extraia o tipo se quiser
                midia_id = cursor.fetchone()[0]
                id_midias.append(midia_id)

            # Inserir risco
            cursor.execute("""
                INSERT INTO riscos (
                    id_usuario,
                    latitude,
                    longitude,
                    endereco,
                    classificacao,
                    descricao,
                    id_midias
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                usuario_id,
                float(latitude),  
                float(longitude),
                endereco,
                classificacao,
                descricao,
                id_midias if id_midias else None,
            ))

            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"cadastro endereco: {endereco}")
            logger.debug(f"cadastro descricao: {descricao}")
            logger.debug(f"cadastro midias: {midias}")
            logger.debug(f"cadastro nome: {nome}")
            logger.debug(f"cadastro whatsapp_id: {whatsapp_id}")
            logger.debug(f"cadastro classificacao: {classificacao}")

            enviar_risco_para_wordpress(
                endereco=endereco,
                descricao=descricao,
                midias_paths=midias,
                latitude=latitude,
                longitude=longitude,
                nome_completo=nome,
                email="anonimo@nossasdcp.org.br",
                telefone=whatsapp_id,
                autoriza_contato=False,
                classificacao=classificacao,
            )

        except Exception as e:
            dispatcher.utter_message(text="Erro ao salvar os dados do risco.")
            logger.error(f"[ERRO SALVAMENTO RISCO] {e}", exc_info=True)
            return []

        dispatcher.utter_message(
            text='✅ *Registrado!*\nEstamos verificando suas informações. Assim que a revisão for concluída, você receberá uma mensagem de confirmação.'
        )
        dispatcher.utter_message(
            text='⛑️ Se precisar de ajuda urgente, ligue para a *Defesa Civil – 199.*', 
        )
        
        dispatcher.utter_message(
            text='ℹ️ Te ajudo em algo mais? Você pode clicar em:',
            buttons=[
                {"title": "Voltar ao menu", "payload": "/menu_inicial"},
                {"title": "Como tá minha área", "payload": "/como_ta_minha_area"},
                {"title": "Encerrar", "payload": "/sair"}
            ]
        )

        return [SlotSet("classificacao_risco", None),
            SlotSet("descricao_risco", None),
            SlotSet("endereco", None),
            SlotSet("latitude", None),
            SlotSet("longitude", None),
            SlotSet("midias", []),
            SlotSet("contexto_endereco_corrigido", False), 
            SlotSet("contexto_classificacao_corrigida", False)
            ]

class ActionListarRiscos(Action):
    def name(self) -> str:
        return "action_listar_riscos"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_listar_riscos")
        last_action = None
        last_action = get_last_action(tracker)
        pagina = tracker.get_slot("pagina_risco") or 1
        if last_action != "action_listar_riscos" and last_action != "action_perguntar_mais_riscos":
            logger.debug(f"Last action:: {last_action}")
            pagina = 1

        wordpress_url = os.getenv("WORDPRESS_URL")
        if not wordpress_url:
            dispatcher.utter_message(text="Erro de configuração: URL do WordPress não definida.")
            logger.error("WORDPRESS_URL não está definida nas variáveis de ambiente.")
            return []

        endpoint = f"{wordpress_url}wp-json/dcp/v1/riscos?per_page=1&page={pagina}"
        logger.debug(f"Buscando riscos na URL: {endpoint}")

        try:
            response = requests.get(endpoint)
            logger.debug(f"Resposta HTTP: {response.status_code} - {response.text}")
            response.raise_for_status()
            dados = response.json()
            riscos = extrair_riscos(dados)

            if not riscos:
                dispatcher.utter_message(text="Não temos mais relatos na sua região.")
                return [SlotSet("pagina_risco", 1)]
            
            mensagem = ''
            for risco in riscos:
                classificacao = risco['classificacao'][0]
                classificacao_dict = {
                    "Alagamento": "☔️ Alagamento informado",
                    "Lixo": "🗑️ Lixo registrado",
                    "Outros": "🔺 Risco informado"
                }
                classificacao_texto = classificacao_dict.get(classificacao, "")
                data_hora = formata_data(risco['data'],'%H:%M do dia %d/%m/%Y')
                mensagem = (
                    f"{classificacao_texto} às {data_hora}\n \n"
                    f"*Local:* {risco['endereco']}\n \n"
                )
                if risco['descricao']:
                    mensagem += f"*Descrição:* {risco['descricao']}\n\n"
                if risco['imagens'] or risco['videos']:
                    mensagem = mensagem + f"*Fotos/vídeos:*\n \n"
                dispatcher.utter_message(text=mensagem)
                for image in risco['imagens']:
                    dispatcher.utter_message(image=image)
                videos = risco['videos']
                for idx, video in enumerate(videos):
                    is_last = idx == len(videos) - 1
                    logger.debug(f"video: {video}")
                    dispatcher.utter_message(text="", custom={"type": "video", "url": video, 'is_last': is_last})
                dispatcher.utter_message(text="\n \n \n \n")
            
            return [SlotSet("pagina_risco", pagina + 1), FollowupAction("action_perguntar_mais_riscos")]

        except requests.RequestException as e:
            dispatcher.utter_message(text="Ocorreu um erro ao buscar os riscos.")
            logger.error(f"[ERRO] Falha na requisição para {endpoint}: {e}", exc_info=True)
            return []

class ActionPerguntarMaisRiscos(Action):
    def name(self) -> str:
        return "action_perguntar_mais_riscos"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_perguntar_mais_riscos")
        time.sleep(2)
        dispatcher.utter_message(
            text="Quer ver mais relatos da comunidade?",
            buttons=[
                {"title": "Sim", "payload": "/mais_riscos"},
                {"title": "Não", "payload": "/sair_consulta_risco"}
            ]
        )
        return []

class ActionNivelDeRisco(Action):
    def name(self):
        return "action_nivel_de_risco"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_nivel_de_risco")
        wordpress_url = os.getenv("WORDPRESS_URL")
        endpoint = f"{wordpress_url}/wp-json/dcp/v1/risco-regiao"
        SlotSet("pagina_risco",1)

        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data or "grau_risco" not in data:
                dispatcher.utter_message(text="⚠️ Não consegui obter o nível de risco no momento.")
                return []

            nivel = data["grau_risco"]
            mensagem = f"🚨 O nível de risco atual da sua região é: *{nivel.upper()}*."
            dispatcher.utter_message(text=mensagem)

        except Exception as e:
            logger.error(f"Erro ao consultar o nível de risco: {e}")
            dispatcher.utter_message(text="❌ Ocorreu um erro ao buscar o nível de risco.")
        
        return []

class ActionListarAbrigos(Action):
    def name(self):
        return "action_listar_abrigos"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_listar_abrigos")
        try:
            wordpress_url = os.getenv("WORDPRESS_URL")
            endpoint = f"{wordpress_url}/wp-json/dcp/v1/abrigos"

            response = requests.get(endpoint)
            response.raise_for_status()
            abrigos = response.json()

            if not abrigos:
                dispatcher.utter_message(text="Não encontrei nenhum abrigo no momento.")
                return []

            mensagem = "Aqui estão alguns abrigos disponíveis:\n\n"
            for abrigo in abrigos:
                mensagem += f"🏠 *{abrigo['nome']}*\n{abrigo['endereco']}\n\n"

            dispatcher.utter_message(text=mensagem)

        except Exception as e:
            logger.error(f"Erro ao buscar abrigos: {e}")
            dispatcher.utter_message(text="Desculpe, houve um erro ao buscar os abrigos.")
        
        return []
    
class ActionListarContatosEmergencia(Action):
    def name(self):
        return "action_listar_contatos_emergencia"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_listar_contatos_emergencia")

        wordpress_url = os.getenv("WORDPRESS_URL")
        if not wordpress_url:
            dispatcher.utter_message(text="A URL do WordPress não está configurada.")
            return []

        endpoint = f"{wordpress_url}/wp-json/dcp/v1/contatos"

        try:
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()
            contatos = response.json()

            if not contatos:
                dispatcher.utter_message(text="Nenhum contato de emergência encontrado.")
                return []

            mensagens = []
            for contato in contatos:
                nome = contato.get("nome", "Nome não disponível")
                descricao = contato.get("descricao", "")
                telefone = contato.get("telefone", "Telefone não disponível")
                mensagens.append(f"*{nome}*: {telefone}")
                mensagens.append(f"\n{descricao}")

            mensagem_final = "Contatos de emergência:\n" + "\n".join(mensagens)
            dispatcher.utter_message(text=mensagem_final)

        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="Não foi possível obter os contatos de emergência no momento.")
            print(f"Erro ao acessar o endpoint: {e}")

        return []

class ActionBuscarDicas(Action):
    def name(self):
        return "action_buscar_dicas"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_buscar_dicas")
        tipo_dica = tracker.get_slot("dicas")
        if not tipo_dica:
            dispatcher.utter_message(text="Desculpe, não entendi o tipo de dica que você deseja.")
            return []

        wordpress_url = os.getenv("WORDPRESS_URL")
        if not wordpress_url:
            dispatcher.utter_message(text="Erro: URL do WordPress não configurada.")
            return []

        endpoint = f"{wordpress_url}/wp-json/dcp/v1/dicas?tipo={tipo_dica}"
        try:
            response = requests.get(endpoint, timeout=5)
            response.raise_for_status()
            dicas = response.json()

            if not dicas:
                dispatcher.utter_message(text=f"Não encontrei dicas para '{tipo_dica}'.")
                return []

            mensagem = f"Dicas para {tipo_dica}:\n"
            for dica in dicas:
                mensagem += f"- {dica}\n"

            dispatcher.utter_message(text=mensagem)
        except requests.RequestException as e:
            dispatcher.utter_message(text="Desculpe, ocorreu um erro ao buscar as dicas.")
            # Aqui você pode adicionar um log do erro, se desejar
        return []
    
    
    from rasa_sdk import Action

class ActionPerguntaNotificacoes(Action):
    def name(self) -> str:
        return "action_pergunta_notificacoes"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_pergunta_notificacoes")
        whatsapp_id = tracker.sender_id

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Busca o campo 'notificacoes' do usuário
            cursor.execute("SELECT notificacoes FROM usuarios WHERE whatsapp_id = %s", (whatsapp_id,))
            result = cursor.fetchone()

            if result is not None:
                notificacoes = result[0]

                if notificacoes:  # Se for True
                    return [FollowupAction("utter_finalizar")]
                elif notificacoes == False:  # Se for False
                    dispatcher.utter_message(
                        text='No momento você optou por não receber notificações. Você deseja alterar?',
                        buttons=[
                            {"title": "Sim", "payload": "/receber_notificacoes"},
                            {"title": "Não", "payload": "/nao_receber_notificacoes"}
                        ]
                    )
                else:
                    # Usuário não encontrado no banco
                    dispatcher.utter_message(
                        text='✅ Certo! Para receber avisos, é só entrar no grupo da Defesa Climática Popular.\nPor lá, avisamos sobre mudanças na sua região.',
                        buttons=[
                            {"title": "Entrar no grupo", "url": "https://chat.whatsapp.com/JrabtO1ww07KbJolQVOi2y"},
                            {"title": "Não", "payload": "/nao_receber_notificacoes"}
                        ]
                    )

            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Erro ao verificar notificações: {e}")
            dispatcher.utter_message(
                text="Houve um problema ao acessar seu cadastro. Por favor, tente novamente mais tarde."
            )

        return []
    
class ActionReceberNotificacoes(Action):
    def name(self) -> str:
        return "action_receber_notificacoes"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_receber_notificacoes")
        # Obtém o número de telefone do usuário (ID da conversa)
        telefone = tracker.sender_id
        try:
            # Conecta ao banco de dados
            conn = get_db_connection()
            cursor = conn.cursor()

            # Atualiza o campo 'notificacoes' para True
            cursor.execute("""
                UPDATE usuarios
                SET notificacoes = TRUE
                WHERE whatsapp_id = %s;
            """, (telefone,))
            conn.commit()
            dispatcher.utter_message(text='Para garantir que as mensagens cheguem corretamente adicione o contato da Defesa Climática Popular na sua agenda.')
            dispatcher.utter_message(text='Toque no número e selecione "Adicionar aos contatos".\nEscolha "Criar novo contato" ou "Atualizar contato existente".\nSalve com um nome fácil de lembrar.')
            dispatcher.utter_message(text='✅ Você agora receberá notificações de emergência. Para não receber mais você pode escrever a qualquer momento "parar de receber notificações".')
        except Exception as e:
            logger.error(f"Erro ao atualizar notificações: {e}")
            dispatcher.utter_message(text="❌ Ocorreu um erro ao ativar as notificações.")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return [FollowupAction("utter_finalizar")]
    
class ActionPararNotificacoes(Action):
    def name(self) -> str:
        return "action_parar_notificacoes"  

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_parar_notificacoes")
        # Obtém o número de telefone do usuário (ID da conversa)
        telefone = tracker.sender_id
        try:
            # Conecta ao banco de dados
            conn = get_db_connection()
            cursor = conn.cursor()

            # Atualiza o campo 'notificacoes' para True
            cursor.execute("""
                UPDATE usuarios
                SET notificacoes = FALSE
                WHERE whatsapp_id = %s;
            """, (telefone,))
            conn.commit()

            dispatcher.utter_message(text='✅ Vocẽ não receberá notificações!')
        except Exception as e:
            logger.error(f"Erro ao atualizar notificações: {e}")
            dispatcher.utter_message(text="❌ Ocorreu um erro ao remover as notificações.")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return [FollowupAction("utter_finalizar")]

    
class ActionSair(Action):
    def name(self) -> str:
        return "action_sair"

    def run(self, dispatcher, tracker, domain):
        logger.debug("rodando action: action_sair")
        dispatcher.utter_message(text="Certo! Se quiser mais informações é só mandar um “oi” por aqui. \n \nVocê também pode acompanhar atualizações no site www.defesaclimaticapopular.org\n\n")
        dispatcher.utter_message(text="E, se quiser receber avisos sobre sua região, entre no grupo da Defesa Climática Popular pelo link bit.ly/grupodefesaclimaticapopular. \n \nPor lá, avisamos quando houver mudanças ou novidades no Jacarezinho.")
        dispatcher.utter_message(text="Estamos por aqui pra ajudar no que for possível! 🫂")
        trigger_date_time = datetime.now(pytz.timezone("America/Sao_Paulo")) - timedelta(minutes=3)
        return [ ReminderScheduled(
                "inatividade_timeout",
                trigger_date_time = trigger_date_time,
                name="lembrete_inatividade",
                kill_on_user_message=True
            ),
            SlotSet("classificacao_risco", None),
            SlotSet("descricao_risco", None),
            SlotSet("endereco", None),
            SlotSet("latitude", None),
            SlotSet("longitude", None),
            SlotSet("midias", []),
            SlotSet("contexto_endereco_corrigido", False), 
            SlotSet("contexto_classificacao_corrigida", False)
            ]
