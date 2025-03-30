from rasa_sdk import Action
from rasa_sdk.events import UserUtteranceReverted, SlotSet
import requests
import json
import logging
import sys
import sqlite3
from rasa_sdk.events import FollowupAction
from rasa_sdk.executor import CollectingDispatcher

logging.basicConfig(level=logging.DEBUG)  # Força o nível global de debug
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 

class ActionFallbackButtons(Action):
    def name(self):
        return "action_fallback_buttons"

    def run(self, dispatcher, tracker, domain):
        logger.debug("Fallback! fallback!!")

        nome = tracker.get_slot("nome")
        if not nome:
            return [FollowupAction("action_perguntar_nome")]

        # Verifica se a última ação foi action_ask_descricao_risco
        last_action = None
        for event in reversed(tracker.events):
            if event.get("event") == "action":
                last_action = event.get("name")
                break

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
        logger.debug(f"solicitando localização")
        dispatcher.utter_message(text="Ok! agora precisamos saber onde está o risco que você deseja compartilhar. Você pode clicar no botão para compartilhar ou escrever um endereço se estiver usando o WhastApp Web.",custom={"type": "location_request"})
        return []
from rasa_sdk import Action

class ActionRepeatLastMessage(Action):
    def name(self):
        return "action_repeat_last_message"

    def run(self, dispatcher, tracker, domain):
        last_bot_messages = []

        for event in reversed(tracker.events):
            if event.get("event") == "bot":
                last_bot_messages.append(event.get("text"))
                if len(last_bot_messages) == 2:
                    break

        if len(last_bot_messages) == 2:
            penultima_mensagem = last_bot_messages[1]
            dispatcher.utter_message(text=penultima_mensagem)
        elif last_bot_messages:
            dispatcher.utter_message(text=last_bot_messages[0])
        else:
            dispatcher.utter_message(text="Desculpe, não consigo repetir a última mensagem.")

        return []


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
                            {"title": "Sim", "payload": "/affirm"},
                            {"title": "Não", "payload": "/deny"}
                        ]
                    )
                    return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco)]
                else:
                    dispatcher.utter_message(text="Desculpe, não consegui encontrar o endereço. Vamos tentar de novo.")
                    return [FollowupAction("action_perguntar_nome")]
            else:
                logger.debug(f"tem endereço")
                endereco = location_data['address']
                dispatcher.utter_message(
                    text=f"Encontrei esse endereço: {endereco}\n Está correto?",
                    buttons=[
                        {"title": "Sim", "payload": "/affirm"},
                        {"title": "Não", "payload": "/deny"}
                    ]
                )
                
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
                        {"title": "Sim", "payload": "/affirm"},
                        {"title": "Não", "payload": "/deny"}
                    ]
                )
                return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco)]
            else:
                dispatcher.utter_message(text="Não encontrei esse endereço. Você pode tentar novamente?")
                return []
        else:
            dispatcher.utter_message(text="Desculpe, não consegui buscar o endereço agora. Vamos tentar de novo.")
            return [FollowupAction("action_perguntar_nome")]



class ActionSalvarNome(Action):
    def name(self):
        return "action_salvar_nome"

    def run(self, dispatcher, tracker, domain):
        nome = tracker.get_slot("nome")
        whatsapp_id = tracker.sender_id

        if nome:
            try:
                conn = sqlite3.connect("usuarios.db")
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        whatsapp_id TEXT UNIQUE,
                        nome TEXT
                    )
                """)
                cursor.execute("""
                    INSERT INTO usuarios (whatsapp_id, nome)
                    VALUES (?, ?)
                    ON CONFLICT(whatsapp_id) DO UPDATE SET nome = excluded.nome
                """, (whatsapp_id, nome))
                conn.commit()
                conn.close()
            except Exception as e:
                dispatcher.utter_message(text="Ocorreu um erro ao salvar seu nome.")
                print(f"[ERRO BANCO] {e}")
        else:
            dispatcher.utter_message(text="Não consegui entender seu nome.")

        return []

class ActionPerguntarNome(Action):
    def name(self):
        return "action_perguntar_nome"

    def run(self, dispatcher, tracker, domain):
        nome = tracker.get_slot("nome")
        if nome:
            dispatcher.utter_message(
                text=f"O nome {nome} está correto?",
                buttons=[
                    {"title": "Sim", "payload": "/affirm"},
                    {"title": "Não", "payload": "/deny"}
                ]
            )
        else:
            dispatcher.utter_message(text="Olá! Aqui é o chatbot da Defesa Climática Popular. Como posso te chamar?\nNão se preocupe pois manteremos o sigilo.")
        return []

class ActionApagarNome(Action):
    def name(self):
        return "action_apagar_nome"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("nome", None)]
    


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
            return [FollowupAction("utter_perguntar_por_midia")]
        else:
            dispatcher.utter_message(text="Não consegui entender a descrição, tente novamente.")
            return [FollowupAction("action_ask_descricao_risco")]

class ActionConfirmarRisco(Action):
    def name(self) -> str:
        return "action_confirmar_relato"

    def run(self, dispatcher,
            tracker,
            domain):

        nome = tracker.get_slot("nome") or "não informado"
        endereco = tracker.get_slot("endereco") or "não informado"
        classificacao = tracker.get_slot("classificacao_risco") or "não informado"

        mensagem = (
            f"Resumo do seu relato:\n"
            f"👤 Nome: {nome}\n"
            f"📍 Endereço: {endereco}\n"
            f"⚠️ Classificação do risco: {classificacao}\n\n"
            f"Essas informações estão corretas?"
        )

        dispatcher.utter_message(
            text=mensagem,
            buttons=[
                {"title": "Sim", "payload": "/affirm"},
                {"title": "Não", "payload": "/deny"}
            ]
        )

        return []