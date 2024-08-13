import copy
import json
import speech_recognition as sr
from fastapi import WebSocket, WebSocketDisconnect

from app.common.utils import logger
from app.constants import InstantOffer
from app.service.helper.openai import OpenAI
from app.service.helper.handle_audio import AudioHandler
from app.common.web_socket_utils import websocket_manager
from app.service.instant_offer_automation import InstantOfferAutomation


class InstantOfferGenerator:
    def __init__(self):
        self.openai = OpenAI()
        self.recognizer = sr.Recognizer()
        self.audio_handle = AudioHandler()
        self.instant_offer_automation = InstantOfferAutomation(self.openai)

    async def _handle_error(self, error: Exception, channel_id: str):
        error_message = str(error)
        broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
        broadcast_response['error']['message'] = error_message
        await websocket_manager.broadcast(broadcast_response, channel_id)
        logger.info(f"Error: {error_message}")
        await websocket_manager.broadcast({"error": f"An error occurred: {str(error)}"}, channel_id)

    async def handle_socket_connection(self, websocket: WebSocket, channel_id: str):
        await websocket_manager.connect(websocket, channel_id)

        try:
            while True:
                message = await websocket.receive()

                if message.get('text'):
                    socket_event = json.loads(message.get('text'))
                    if socket_event['type'] == 'acknowledge':
                        logger.info(f"Received acknowledgment from channel {socket_event.get('channelId')}")
                        await self.instant_offer_automation.get_response(websocket, channel_id)

        except WebSocketDisconnect:
            logger.info(f"Client disconnected from channel {channel_id}")
        except Exception as e:
            await self._handle_error(e, channel_id)
