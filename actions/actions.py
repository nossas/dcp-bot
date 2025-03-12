from rasa_sdk import Action
from rasa_sdk.events import UserUtteranceReverted, SlotSet
import requests
import json
import logging
import sys

logging.basicConfig(level=logging.DEBUG)  # Força o nível global de debug
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) 
class ActionFallbackButtons(Action):
    def name(self):
        return "action_fallback_buttons"

    def run(self, dispatcher, tracker, domain):
        logger.debug(f"Fallback! fallback!!")

        # Obtém a última mensagem enviada pelo bot
        last_bot_message = None
        for event in reversed(tracker.events):
            if event.get("event") == "bot":
                last_bot_message = event.get("text")
                break

        # Mensagem de fallback
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
        dispatcher.utter_message(custom={"type": "location_request"})
        return []

class ActionRepeatLastMessage(Action):
    def name(self):
        return "action_repeat_last_message"

    def run(self, dispatcher, tracker, domain):
        last_bot_message = None
        for event in reversed(tracker.events):
            if event.get("event") == "bot":
                last_bot_message = event.get("text")
                break

        if last_bot_message:
            dispatcher.utter_message(text=last_bot_message)
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
                logger.debug(f"não tem endereço")                
                logger.debug(f"latitude: {latitude}")
                logger.debug(f"longitude: {longitude}")
                url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"
                headers = {"User-Agent": "MeuBot/0.1 (email@exemplo.com)"}
                response = requests.get(url, headers=headers)
                logger.debug(f"Received response: {response}")
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Received data: {data}")

                    endereco = data.get("display_name", "Endereço não encontrado.")
                    dispatcher.utter_message(text=f"Encontrei esse endereço: {endereco}")
                    return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco)]
                else:
                    dispatcher.utter_message(text="Desculpe, não consegui encontrar o endereço.")
                    return []
            else:
                logger.debug(f"tem endereço")                
                dispatcher.utter_message(text=f"Seu endereço é {location_data['address']}")
                
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
                endereco_encontrado = data[0].get("display_name", "Endereço não encontrado.")
                latitude = data[0].get("lat")
                longitude = data[0].get("lon")

                dispatcher.utter_message(text=f"Encontrei esse endereço: {endereco_encontrado}")
                return [SlotSet("latitude", latitude), SlotSet("longitude", longitude), SlotSet("endereco", endereco_encontrado)]
            else:
                dispatcher.utter_message(text="Não encontrei esse endereço. Você pode tentar novamente?")
                return []
        else:
            dispatcher.utter_message(text="Desculpe, não consegui buscar o endereço agora.")
            return []
