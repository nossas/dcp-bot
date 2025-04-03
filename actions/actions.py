from rasa_sdk import Action
from rasa_sdk.events import UserUtteranceReverted, SlotSet
import requests
import json
import logging
import sys
import sqlite3
from rasa_sdk.events import FollowupAction
from rasa_sdk.executor import CollectingDispatcher
import yaml
from .db_utils import get_db_connection

logging.basicConfig(level=logging.DEBUG)  # Força o nível global de debug
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

class ActionFallbackButtons(Action):
    def name(self):
        return "action_fallback_buttons"

    def run(self, dispatcher, tracker, domain):
        logger.debug("Fallback! fallback!!")

        last_action = None
        for event in reversed(tracker.events):
            if event.get("event") == "action" and event.get("name") not in ["action_listen","action_repeat_last_message","action_fallback_buttons"]:
                last_action = event.get("name")
                break
        logger.debug(f"Last action:{last_action}")
        if last_action == "action_perguntar_nome":
            user_message = tracker.latest_message.get("text")
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
            return [
                SlotSet("descricao_risco", user_message),
                FollowupAction("utter_perguntar_por_midia")
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

        dispatcher.utter_message(text="Não compreendi, escolha uma opção:", buttons=buttons)
        return [UserUtteranceReverted()]

class ActionRequestLocation(Action):
    def name(self):
        return "action_request_location"

    def run(self, dispatcher, tracker, domain): 
        
        latitude = tracker.get_slot("latitude")
        longitude = tracker.get_slot("longitude")
        endereco = tracker.get_slot("endereco")
        nome = tracker.get_slot("nome")
        classificacao_risco = tracker.get_slot("classificacao_risco")
        if endereco and nome and classificacao_risco:
            dispatcher.utter_message(
                text="Você já iniciou o processo para relatar uma stuação de risco.",
                buttons=[
                    {"title": "Começar de novo", "payload": "/apagar_risco"},
                    {"title": "Continuar/Corrigir", "payload": "/continuar_risco"}
                ]
            )
            return[]
        SlotSet("classificacao_risco", None),
        SlotSet("descricao_risco", None),
        SlotSet("endereco", None),
        SlotSet("latitude", None),
        SlotSet("longitude", None),
        SlotSet("midias", None),
        SlotSet("identificar", None),                  
        logger.debug(f"solicitando localização")
        dispatcher.utter_message(text="Ok! agora precisamos saber onde está o risco que você deseja compartilhar. Você pode clicar no botão para compartilhar ou escrever um endereço se estiver usando o WhastApp Web.",custom={"type": "location_request"})
        return []

class ActionApagarRisco(Action):
    def name(self):
        return "action_apagar_risco"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Ok, vamos recomeçar.")
        return [
            SlotSet("classificacao_risco", None),
            SlotSet("descricao_risco", None),
            SlotSet("endereco", None),
            SlotSet("latitude", None),
            SlotSet("longitude", None),
            SlotSet("midias", []),
            SlotSet("identificar", None),
        ]

class ActionRetomarRisco(Action):
    def name(self):
        return "retomar_risco"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Ok, vamos retomar.")
        return[]

class ActionRepeatLastMessage(Action):
    def name(self):
        return "action_repeat_last_message"

    def run(self, dispatcher, tracker, domain):
        last_bot_messages = []
        last_action = None
        for event in reversed(tracker.events):
            if event.get("event") == "action" and event.get("name") not in ["action_listen","action_repeat_last_message","action_fallback_buttons"]:
                last_action = event.get("name")
                break
        logger.debug(f"Last action:{last_action}")
        
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

class ActionRetomaRisco(Action):
    def name(self) -> str:
        return "action_retoma_risco"

    def run(self, dispatcher,
            tracker,
            domain):
        slots = {
            "classificacao_risco": tracker.get_slot("classificacao_risco"),
            "descricao_risco": tracker.get_slot("descricao_risco"),
            "endereco": tracker.get_slot("endereco"),
            "midias": tracker.get_slot("midias"),
            "identificar": tracker.get_slot("identificar"),
        }
        if slots['endereco']:
            if slots['classificacao_risco']:
                return[FollowupAction("action_ask_descricao_risco")]
            return[FollowupAction("utter_classificar_risco")]
        return[FollowupAction("action_request_location")]
    
class ActionPerguntarNome(Action):
    def name(self):
        return "action_perguntar_nome"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        nome = tracker.get_slot("nome")
        if nome:
            logger.error(f"Nome no Slot")

            dispatcher.utter_message(
                text=f"O nome {nome} está correto?",
                buttons=[
                    {"title": "Sim", "payload": "/affirm_name"},
                    {"title": "Não", "payload": "/deny_name"}
                ]
            )
            return []

        try:
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM usuarios WHERE whatsapp_id = %s", (sender_id,))
                row = cursor.fetchone()
                cursor.close()
                conn.close()

                if row:
                    logger.error(f"Nome no banco")

                    nome = row[0]
                    dispatcher.utter_message(
                        text=f"O nome {nome} está correto?",
                        buttons=[
                            {"title": "Sim", "payload": "/affirm_name"},
                            {"title": "Não", "payload": "/deny_name"}
                        ]
                    )
                    return [SlotSet("nome", nome)]

        except Exception as e:
            logger.error(f"Erro ao buscar nome no banco: {e}")

        dispatcher.utter_message(
            text="Olá! Aqui é o chatbot da Defesa Climática Popular. Como posso te chamar?\nNão se preocupe pois manteremos o sigilo."
        )
        return []

class ActionSalvarNome(Action):
    def name(self):
        return "action_salvar_nome"

    def run(self, dispatcher, tracker, domain):
        nome = tracker.latest_message.get("text") if tracker.latest_message.get("text") != '/affirm_name' else tracker.get_slot("nome")
        whatsapp_id = tracker.sender_id

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

        return [SlotSet("nome", nome)]

class ActionApagarNome(Action):
    def name(self):
        return "action_apagar_nome"

    def run(self, dispatcher, tracker, domain):
        logger.debug("Apagando nome do slot e do banco.")

        whatsapp_id = tracker.sender_id

        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM usuarios WHERE whatsapp_id = %s;",
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
        return [SlotSet("nome", None)]
    
class ActionBuscarEnderecoOpenStreet(Action):
    def name(self):
        return "action_buscar_endereco_openstreet"

    def run(self, dispatcher, tracker, domain):
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
                url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"
                headers = {"User-Agent": "MeuBot/0.1 (email@exemplo.com)"}
                response = requests.get(url, headers=headers)
                logger.debug(f"Received response: {response}")
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Received data: {data}")

                    endereco = data.get("display_name", "Endereço não encontrado.")
                    dispatcher.utter_message(
                        text=f"Encontrei esse endereço: {endereco}\n Está correto?",
                        buttons=[
                            {"title": "Sim", "payload": "/affirm_address"},
                            {"title": "Não", "payload": "/deny_address"}
                        ]
                    )
                    return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco)]
                else:
                    dispatcher.utter_message(text="Desculpe, não consegui encontrar o endereço.tente novamente.")
                    return [FollowupAction("action_request_location")]
            else:
                logger.debug(f"tem endereço")
                endereco = location_data['address']
                dispatcher.utter_message(
                    text=f"Encontrei esse endereço: {endereco}\n Está correto?",
                    buttons=[
                        {"title": "Sim", "payload": "/affirm_address"},
                        {"title": "Não", "payload": "/deny_address"}
                    ]
                )
                return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco)]

                
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

class ActionBuscarEnderecoTextoOpenStreet(Action):
    def name(self):
        return "action_buscar_endereco_texto_openstreet"

    def run(self, dispatcher, tracker, domain):
        endereco_texto = tracker.latest_message.get("text")
        logger.debug(f"Buscando endereço pelo texto: {endereco_texto}")
        
        url = f"https://nominatim.openstreetmap.org/search?q={endereco_texto}&format=json&limit=1"
        headers = {"User-Agent": "MeuBot/0.1 (email@exemplo.com)"}
        
        response = requests.get(url, headers=headers)
        logger.debug(f"Resposta do Nominatim (texto): {response.status_code} - {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data:
                endereco = data[0].get("display_name", "Endereço não encontrado.")
                latitude = data[0].get("lat")
                longitude = data[0].get("lon")

                dispatcher.utter_message(
                    text=f"Encontrei esse endereço: {endereco}\n Está correto?",
                    buttons=[
                        {"title": "Sim", "payload": "/affirm_address"},
                        {"title": "Não", "payload": "/deny_address"}
                    ]
                )
                return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco)]
            else:
                dispatcher.utter_message(text="Não encontrei esse endereço. tente novamente.")
                return [FollowupAction("action_request_location")]
        else:
            dispatcher.utter_message(text="Desculpe, não consegui buscar o endereço agora. Vamos tentar de novo.")
            return [FollowupAction("action_request_location")]

class ActionSalvarClassificacaoRisco(Action):
    def name(self) -> str:
        return "action_salvar_classificacao_risco"

    def run(self, dispatcher: CollectingDispatcher,
            tracker,
            domain):
        
        risco = tracker.get_slot("classificacao_risco")
        logger.debug(risco)

        if risco:
            return [
                SlotSet("classificacao_risco", risco),
                FollowupAction("action_ask_descricao_risco")
            ]        
        else:
            dispatcher.utter_message(text="Não consegui entender a classificação do risco.")
            return [FollowupAction("utter_classificar_risco")]

class ActionSolicitarDescricaoRisco(Action):
    def name(self) -> str:
        return "action_ask_descricao_risco"

    def run(self, dispatcher,
            tracker,
            domain):
        
        risco = tracker.get_slot("classificacao_risco")

        if risco:
            dispatcher.utter_message(
                text=f"Entendido, você classificou o risco como: {risco}. Por favor escreva mais informações sobre o risco ou clique em pular.",
                buttons=[
                    {"title": "Pular", "payload": "/pular_descricao_risco"},
                ]
            )
            return []        
        else:
            dispatcher.utter_message(text="Não consegui entender a classificação do risco.")
            return [FollowupAction("utter_classificar_risco")]

class ActionSalvarDescricaoRisco(Action):
    def name(self) -> str:
        return "action_salvar_descricao_risco"
    def run(self, dispatcher,
            tracker,
            domain):
        descricao = tracker.get_slot("descricao_risco")
        if descricao:
            dispatcher.utter_message(text="Obrigado pela descrição!")
            return [FollowupAction("utter_perguntar_por_midia")]
        else:
            dispatcher.utter_message(text="Não consegui entender a descrição, tente novamente.")
            return [FollowupAction("action_ask_descricao_risco")]

class ActionSalvarMidiaRisco(Action):
    def name(self) -> str:
        return "action_salvar_midia_risco"

    def run(self, dispatcher, tracker, domain):
        try:
            user_message = tracker.latest_message.get("text")
            midia_data = json.loads(user_message)

            midias_slot = tracker.get_slot("midias") or []

            if midia_data.get("tipo") == "mídia_combinada":
                novas_midias = [m["path"] for m in midia_data["midias"]]
                midias_slot.extend(novas_midias)
                dispatcher.utter_message(text=f"{len(novas_midias)} mídias adicionadas!")
            else:
                # Caso venha uma mídia só
                path = midia_data["path"]
                midias_slot.append(path)
                dispatcher.utter_message(text="Foto/vídeo adicionado!")

            return [SlotSet("midias", midias_slot)]

        except Exception as e:
            dispatcher.utter_message(text="Ocorreu um erro ao salvar mídia.")
            logger.error(f"Erro ao salvar mídia no slot: {e}")
            return []

class ActionConfirmarRisco(Action):
    def name(self) -> str:
        return "action_confirmar_relato"

    def run(self, dispatcher,
            tracker,
            domain):

        nome = tracker.get_slot("nome") or "não informado"
        endereco = tracker.get_slot("endereco") or "não informado"
        classificacao = tracker.get_slot("classificacao_risco") or "não informado"
        descricao = tracker.get_slot("descricao_risco") or "não informado"

        mensagem = (
            f"Resumo do seu relato:\n"
            f"👤 Nome: {nome}\n"
            f"📍 Endereço: {endereco}\n"
            f"⚠️ Classificação do risco: {classificacao}\n\n"
            f"⚠️ Descrição do risco: {descricao}\n\n"
            f"Essas informações estão corretas?"
        )

        dispatcher.utter_message(
            text=mensagem,
            buttons=[
                {"title": "Sim", "payload": "/afirmar_confirmacao_risco"},
                {"title": "Não", "payload": "/recusar_confirmacao_risco"}
            ]
        )

        return []

class ActionSalvarRisco(Action):
    def name(self) -> str:
        return "action_solicitar_compartilhar_risco"

    def run(self, dispatcher,
            tracker,
            domain):
        # aqui vai a logica de cadastrar o risco no Mapa
        
        dispatcher.utter_message(
            text='Se precisar de ajuda urgente, entre em contato com a Defesa Civil – 199.', #verificar a possibilidade de um template para chamar uma call-to-action com ligação externa.
            
        )
        dispatcher.utter_message(
            text='Obrigado, seu alerta foi registrado mas ainda não foi validado e não aparece no mapa oficial, mas você pode encaminhá-lo para outras pessoas para alertá-las sobre a situação. Você gostaria de compartilhar?',
             buttons=[
                {"title": "Sim", "payload": "/compartilhar_mensagem_risco"},
                {"title": "Não", "payload": "/nao_compartilhar_mensagem_risco"}
            ]
        )

        return []

class ActionFinalizaRisco(Action):
    def name(self) -> str:
        return "action_finaliza_risco"

    def run(self, dispatcher,
            tracker,
            domain):

        return [SlotSet("classificacao_risco", None),
        SlotSet("descricao_risco", None),
        SlotSet("endereco", None),
        SlotSet("latitude", None),
        SlotSet("longitude", None),
        SlotSet("midias", []),
        SlotSet("identificar", None)]