import logging
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Dict, Text, Any, Callable, Awaitable, Optional, List

from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel
from heyoo import WhatsApp
import json

from collections import defaultdict
import asyncio
logger = logging.getLogger(__name__)

class WhatsAppOutput(WhatsApp, OutputChannel):
    """Output channel for WhatsApp Cloud API"""

    @classmethod
    def name(cls) -> Text:
        return "whatsapp"

    def __init__(self, auth_token: Optional[Text], phone_number_id: Optional[Text]) -> None:
        super().__init__(auth_token, phone_number_id=phone_number_id)
    
    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        """Sends text message"""
        for message_part in text.strip().split("\n\n"):
            self.send_message(message_part, recipient_id=recipient_id)
    
    async def send_custom_json(self,recipient_id, custom, **kwargs: Any) -> None:
        if custom.get('type') == "location_request":
            json={
               "messaging_product": "whatsapp",
               "recipient_type": "individual",
               "type": "interactive",
               "to": recipient_id,
               "interactive": {
                   "type": "location_request_message",
                   "body": {
                   "text": "Envie a localização"
                   },
                   "action": {
                   "name": "send_location"
                   }
               }
            }
            WhatsApp.send_custom_json(self,data=json, recipient_id=recipient_id)
            

    async def send_text_with_buttons(
        self, recipient_id: Text, text: Text, buttons: List[Dict[Text, Any]], **kwargs: Any
    ) -> None:
        """Sends text message with buttons"""
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
        """Sends an image."""
        self.send_image(image, recipient_id=recipient_id)

    async def send_video_url(self, recipient_id: Text, video: Text, **kwargs: Any) -> None:
        """Sends a Video"""
        self.send_video(video, recipient_id=recipient_id)

    async def send_document_url(self, recipient_id: Text, document: Text, **kwargs: Any) -> None:
        """Sends a Document"""
        self.send_document(document, recipient_id=recipient_id)

    async def send_audio_url(self, recipient_id: Text, audio: Text, **kwargs: Any) -> None:
        """Sends an Audio"""
        self.send_audio(audio, recipient_id=recipient_id)

class WhatsAppInput(InputChannel):
    """WhatsApp Cloud API input channel"""
    media_cache = defaultdict(list)
    media_timers = {}
    
    @classmethod
    def name(cls) -> Text:
        return "whatsapp"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
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
        self.auth_token = auth_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.debug_mode = debug_mode
        self.client = WhatsApp(self.auth_token, phone_number_id=self.phone_number_id)

        # Log do auth_token para depuração
        logger.debug(f"WhatsAppInput initialized with auth_token: {self.auth_token}")
    
    async def handle_media(self, sender_id, media_object, on_new_message, out_channel):
        if sender_id not in self.media_cache:
            self.media_cache[sender_id] = []
        self.media_cache[sender_id].append(media_object)

        if sender_id in self.media_timers:
            self.media_timers[sender_id].cancel()

        self.media_timers[sender_id] = asyncio.create_task(
            self.finalize_media_batch(sender_id, on_new_message, out_channel)
        )

    async def finalize_media_batch(self, sender_id, on_new_message, out_channel):
        try:
            await asyncio.sleep(3)
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

    def get_message(self, data):
        message_type = self.client.get_message_type(data)
        if message_type == "interactive":
            response = self.client.get_interactive_response(data)
            if response.get("type") == "button_reply":
                return response["button_reply"]["id"]
        if message_type == "location":
            response =  self.client.get_location(data)
            json_string = json.dumps(response)
            return json_string
        return self.client.get_message(data)

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[Any]]) -> Blueprint:
        whatsapp_webhook = Blueprint("whatsapp_webhook", __name__)

        @whatsapp_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @whatsapp_webhook.route("/webhook", methods=["GET"])
        async def verify_token(request: Request) -> HTTPResponse:
            if request.args.get("hub.verify_token") == self.verify_token:
                return response.text(request.args.get("hub.challenge"))
            logger.error("Webhook Verification failed")
            return response.text("Invalid verification token", status=403)

        @whatsapp_webhook.route("/webhook", methods=["POST"])
        async def message(request: Request) -> HTTPResponse:
            logger.debug(f"full message: {request.json}")

            sender = self.client.get_mobile(request.json)
            message_type = self.client.get_message_type(request.json)
            metadata = self.get_metadata(request)
            out_channel = self.get_output_channel()

            if message_type in ["image", "video"]:
                media_data = self.client.get_video(request.json) if message_type == "video" else self.client.get_image(request.json)
                logger.error(f"media_data: {media_data}")

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
                except Exception as e:
                    logger.error(f"Exception when handling message: {e}", exc_info=True)
                    if self.debug_mode:
                        raise

            return response.text("", status=200)

        return whatsapp_webhook

    def get_output_channel(self) -> OutputChannel:
        return WhatsAppOutput(self.auth_token, self.phone_number_id)
