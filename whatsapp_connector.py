import logging
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Dict, Text, Any, Callable, Awaitable, Optional, List
from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel
from heyoo import WhatsApp
import json
import aiohttp
from collections import defaultdict
import asyncio
import os
logger = logging.getLogger(__name__)


async def agendar_inatividade(sender_id: str):
    """Dispara o intent de monitoramento de inatividade.

    Args:
        sender_id (str): Identificador do remetente no WhatsApp.
    """
    async with aiohttp.ClientSession() as session:
        logger.debug(f"----------------------------------fazendo chamada schedule")
        rasa_url = os.environ.get("RASA_URL")

        async with session.post(
            f"{rasa_url}/conversations/{sender_id}/trigger_intent",
            json={"name": "inatividade_monitoramento", "entities": []}
        ) as response:
            await response.read()

class WhatsAppOutput(WhatsApp, OutputChannel):
    """Canal de saida para a API do WhatsApp Cloud."""

    @classmethod
    def name(cls) -> Text:
        """Retorna o nome do canal de saida.

        Returns:
            Text: Nome do canal.
        """
        return "whatsapp"

    def __init__(self, auth_token: Optional[Text], phone_number_id: Optional[Text]) -> None:
        """Inicializa o canal de saida com credenciais do WhatsApp.

        Args:
            auth_token (Optional[Text]): Token de autenticacao.
            phone_number_id (Optional[Text]): ID do numero de telefone.
        """
        super().__init__(auth_token, phone_number_id=phone_number_id)
    
    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        """Envia uma mensagem de texto.

        Args:
            recipient_id (Text): ID do destinatario.
            text (Text): Conteudo da mensagem.
            **kwargs: Parametros extras (nao usados).
        """
        # self.send_custom_json(recipient_id,{'type': "typing"})

        logger.debug(f"➡️ Enviando mensagem para {recipient_id}: {text}")
        for message_part in text.strip().split("\n\n"):
            self.send_message(message_part, recipient_id=recipient_id)
    
    async def send_custom_json(self,recipient_id, custom, **kwargs: Any) -> None:
        """Envia payloads customizados para o WhatsApp Cloud API.

        Args:
            recipient_id (Text): ID do destinatario.
            custom (Dict): Payload customizado.
            **kwargs: Parametros extras (nao usados).
        """
        logger.debug(f"Enviando custom json para {recipient_id}: {custom}")
        if custom.get('type') == "location_request":
            json={
               "messaging_product": "whatsapp",
               "recipient_type": "individual",
               "type": "interactive",
               "to": recipient_id,
               "interactive": {
                   "type": "location_request_message",
                   "body": {
                   "text": "Envie a localização:"
                   },
                   "action": {
                   "name": "send_location"
                   }
               }
            }
            WhatsApp.send_custom_json(self,data=json, recipient_id=recipient_id)
        elif custom.get('type') == "media_id":
            media_type = custom.get("media_type", "image") 
            media_id = custom.get("media_id")
        
            if media_type not in ["image", "video"] or not media_id:
                logger.warning("Tipo de mídia inválido ou media_id ausente")
            else:
                json = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient_id,
                    "type": media_type,
                    media_type: {
                        "id": media_id
                    }
                }

                WhatsApp.send_custom_json(self, data=json, recipient_id=recipient_id)

        elif custom.get('type') == "video":
            logger.debug(f"Video usando custom recipient: {recipient_id} ")
            self.send_video(custom.get('url'),recipient_id)
            if custom.get('is_last'):
                await asyncio.sleep(2)    
            

    async def send_text_with_buttons(
        self, recipient_id: Text, text: Text, buttons: List[Dict[Text, Any]], **kwargs: Any
    ) -> None:
        """Envia uma mensagem de texto com botoes.

        Args:
            recipient_id (Text): ID do destinatario.
            text (Text): Conteudo da mensagem.
            buttons (List[Dict[Text, Any]]): Botoes no formato esperado.
            **kwargs: Parametros extras (nao usados).
        """
        # self.send_custom_json(recipient_id,{type: "typing"})
        buttons_list = [
            {"type": "reply", "reply": {"id": button["payload"], "title": button["title"]}}
            for button in buttons
        ]

        button_dict = {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": buttons_list},
        }

        self.send_reply_button(recipient_id=recipient_id,button=button_dict )  

    async def send_image_url(self, recipient_id: Text, image: Text, **kwargs: Any) -> None:
        """Envia uma imagem por URL.

        Args:
            recipient_id (Text): ID do destinatario.
            image (Text): URL da imagem.
            **kwargs: Parametros extras (nao usados).
        """
        # self.send_custom_json(recipient_id,{type: "typing"})
        self.send_image(image, recipient_id=recipient_id)

    async def send_video_url(self, recipient_id: Text, video: Text, **kwargs: Any) -> None:
        """Envia um video por URL.

        Args:
            recipient_id (Text): ID do destinatario.
            video (Text): URL do video.
            **kwargs: Parametros extras (nao usados).
        """
        # self.send_custom_json(recipient_id,{type: "typing"})
        self.send_video(video, recipient_id=recipient_id)

    async def send_document_url(self, recipient_id: Text, document: Text, **kwargs: Any) -> None:
        """Envia um documento por URL.

        Args:
            recipient_id (Text): ID do destinatario.
            document (Text): URL do documento.
            **kwargs: Parametros extras (nao usados).
        """
        # self.send_custom_json(recipient_id,{type: "typing"})
        self.send_document(document, recipient_id=recipient_id)

    async def send_audio_url(self, recipient_id: Text, audio: Text, **kwargs: Any) -> None:
        """Envia um audio por URL.

        Args:
            recipient_id (Text): ID do destinatario.
            audio (Text): URL do audio.
            **kwargs: Parametros extras (nao usados).
        """
        # self.send_custom_json(recipient_id,{type: "typing"})
        self.send_audio(audio, recipient_id=recipient_id)

class WhatsAppInput(WhatsApp, InputChannel):
    """Canal de entrada para a API do WhatsApp Cloud."""
    media_cache = defaultdict(list)
    media_timers = {}
    
    @classmethod
    def name(cls) -> Text:
        """Retorna o nome do canal de entrada.

        Returns:
            Text: Nome do canal.
        """
        return "whatsapp"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        """Instancia o canal de entrada a partir das credenciais do Rasa.

        Args:
            credentials (Optional[Dict[Text, Any]]): Credenciais do canal.

        Returns:
            InputChannel: Canal de entrada configurado.
        """
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(
            credentials.get("auth_token"),
            credentials.get("phone_number_id"),
            credentials.get("verify_token"),
        )

    def __init__(
        self,
        auth_token: Optional[Text],
        phone_number_id: Optional[Text],
        verify_token: Optional[Text],
        debug_mode: bool = True,
    ) -> None:
        """Inicializa o canal de entrada com tokens e modo de debug.

        Args:
            auth_token (Optional[Text]): Token de autenticacao.
            phone_number_id (Optional[Text]): ID do numero de telefone.
            verify_token (Optional[Text]): Token de verificacao do webhook.
            debug_mode (bool): Se True, relanca excecoes.
        """
        self.auth_token = auth_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.debug_mode = debug_mode
        self.client = WhatsApp(self.auth_token, phone_number_id=self.phone_number_id)
        super().__init__(auth_token, phone_number_id=phone_number_id)

        # Log do auth_token para depuração
        logger.debug(f"WhatsAppInput initialized with auth_token: {self.auth_token}")
    
    async def handle_media(self, sender_id, media_object, on_new_message, out_channel):
        """Acumula midias e agenda o processamento em lote.

        Args:
            sender_id (Text): ID do remetente.
            media_object (Dict): Metadados da midia.
            on_new_message (Callable): Callback de nova mensagem.
            out_channel (OutputChannel): Canal de saida.
        """
        if sender_id not in self.media_cache:
            self.media_cache[sender_id] = []
        self.media_cache[sender_id].append(media_object)

        if sender_id in self.media_timers:
            self.media_timers[sender_id].cancel()

        self.media_timers[sender_id] = asyncio.create_task(
            self.finalize_media_batch(sender_id, on_new_message, out_channel)
        )

    async def finalize_media_batch(self, sender_id, on_new_message, out_channel):
        """Agrupa midias recebidas e envia como uma unica mensagem.

        Args:
            sender_id (Text): ID do remetente.
            on_new_message (Callable): Callback de nova mensagem.
            out_channel (OutputChannel): Canal de saida.
        """
        try:
            medias = self.media_cache.pop(sender_id, [])
            self.media_timers.pop(sender_id, None)

            combined_payload = json.dumps({
                "tipo": "mídia_combinada",
                "midias": medias
            })

            await on_new_message(
                UserMessage(combined_payload, out_channel, sender_id, input_channel=self.name())
            )
        except asyncio.CancelledError:
            pass
    
    async def send_typing(self, recipient_id,message_id):
        """Marca a mensagem como lida e ativa indicador de digitando.

        Args:
            recipient_id (Text): ID do destinatario.
            message_id (Text): ID da mensagem recebida.
        """
        
        json = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
            "typing_indicator": {
                "type": "text"
            }
        }
        return WhatsApp.send_custom_json(self, data=json, recipient_id=recipient_id)
        
    def get_message(self, data):
        """Extrai o texto ou payload equivalente da mensagem recebida.

        Args:
            data (Dict): Payload do webhook do WhatsApp.

        Returns:
            str: Texto ou payload equivalente.
        """
        message_type = self.client.get_message_type(data)
        if message_type == "interactive":
            response = self.client.get_interactive_response(data)
            if response.get("type") == "button_reply":
                return response["button_reply"]["id"]
        if message_type == "location":
            response =  self.client.get_location(data)
            json_string = json.dumps(response)
            return json_string
        if message_type != "text":
            return ''
        return self.client.get_message(data)

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[Any]]) -> Blueprint:
        """Define as rotas HTTP do webhook do WhatsApp.

        Args:
            on_new_message (Callable): Callback de nova mensagem.

        Returns:
            Blueprint: Blueprint do Sanic com as rotas do webhook.
        """
        whatsapp_webhook = Blueprint("whatsapp_webhook", __name__)

        @whatsapp_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            """Endpoint simples de healthcheck.

            Returns:
                HTTPResponse: Resposta JSON com status.
            """
            return response.json({"status": "ok"})

        @whatsapp_webhook.route("/webhook", methods=["GET"])
        async def verify_token(request: Request) -> HTTPResponse:
            """Valida o token de verificacao do webhook.

            Args:
                request (Request): Requisicao HTTP do Sanic.

            Returns:
                HTTPResponse: Challenge ou erro 403.
            """
            if request.args.get("hub.verify_token") == self.verify_token:
                return response.text(request.args.get("hub.challenge"))
            logger.error("Webhook Verification failed")
            return response.text("Invalid verification token", status=403)

        @whatsapp_webhook.route("/webhook", methods=["POST"])
        async def message(request: Request) -> HTTPResponse:
            """Processa mensagens recebidas do WhatsApp.

            Args:
                request (Request): Requisicao HTTP do Sanic.

            Returns:
                HTTPResponse: Resposta HTTP do webhook.
            """
            logger.debug(f"full message: {request.json}")

            sender = self.client.get_mobile(request.json)
            message_type = self.client.get_message_type(request.json)
            metadata = self.get_metadata(request)
            out_channel = self.get_output_channel()
            message_id = self.client.get_message_id(request.json)
            logger.debug(f"sender: {sender}")
            logger.debug(f"message_id: {message_id}")
            if (message_id and sender):
                reply = self.get_interactive_response(request.json) if self.get_interactive_response(request.json) != None else {}
                reply_buttons = reply.get("button_reply",{}).get("id","") 
                await self.send_typing(sender,message_id)
                if message_type not in ["image", "video"] and reply_buttons not in ["/informar_risco"]:
                    await asyncio.sleep(3)
                # if sender and reply and reply_buttons == "/mais_riscos":
                #     logger.debug(f"maior delay para /mais_riscos")
                #     await asyncio.sleep(10)
                logger.debug(f"Enviando typing para {sender} com message_id {message_id}")
            if message_type in ["image", "video"]:
                media_data = self.client.get_video(request.json) if message_type == "video" else self.client.get_image(request.json)
                await self.send_typing(sender,message_id)
                media_id = media_data.get("id")
                url = self.client.query_media_url(media_id)
                mime_type = media_data.get("mime_type")
                downloaded = self.client.download_media(url, mime_type, f"media/{media_id}")

                media_object = {
                    "mime_type": mime_type,
                    "path": downloaded,
                }

                await self.handle_media(sender, media_object, on_new_message, out_channel)
                return response.text("", status=200)
            if message_type in ["audio"]:
                # responde com mensagem avisando que não é possível enviar áudio
                logger.debug(f"Recebido áudio de {sender}, mas não é possível processar áudio.")
                await out_channel.send_text_message(sender, "Não podemos ouvir áudio, por favor mande escrito.")
                return response.text("", status=200)
                
            # Caso não seja mídia
            text = self.get_message(request.json)
            if sender and text:
                try:
                    logger.debug(f"text: {text}")
                    logger.debug(f"out_channel: {out_channel}")
                    logger.debug(f"sender: {sender}")
                    logger.debug(f"input_channel: {self.name()}")
                    logger.debug(f"metadata: {metadata}")

                    await on_new_message(
                        UserMessage(text, out_channel, sender, input_channel=self.name(), metadata=metadata)
                    )
                    await agendar_inatividade(sender)
                except Exception as e:
                    logger.error(f"Exception when handling message: {e}", exc_info=True)
                    if self.debug_mode:
                        raise

            return response.text("", status=200)

        return whatsapp_webhook

    def get_output_channel(self) -> OutputChannel:
        """Retorna o canal de saida configurado.

        Returns:
            OutputChannel: Canal de saida do WhatsApp.
        """
        return WhatsAppOutput(self.auth_token, self.phone_number_id)
