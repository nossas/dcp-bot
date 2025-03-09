from rasa_sdk import Action
from rasa_sdk.events import UserUtteranceReverted

class ActionFallbackButtons(Action):
    def name(self):
        return "action_fallback_buttons"

    def run(self, dispatcher, tracker, domain):
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

        # Faz o bot esquecer a última entrada do usuário para que ele tente novamente
        return [UserUtteranceReverted()]

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