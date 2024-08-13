import json
import copy
import random
import os.path

from app.constants import InstantOffer
from app.service.helper.handle_audio import AudioHandler
from app.common.web_socket_utils import websocket_manager
from app.service.helper.handle_llm_response import LLMResponseHandler


class InstantOfferAutomation:

    def __init__(self, openai):
        self.openai = openai
        self.audio_handler = AudioHandler()
        self.llm_response_handler = LLMResponseHandler(openai)

    async def __publish_successful_message(self, channel_id, result_json):

        successful_message = InstantOffer.QUESTIONS['successful_terminate']
        success_file_path = await self.openai.text_to_speech(successful_message, "successful_message")
        success_file_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", success_file_path)

        broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
        broadcast_response['terminate']['path'] = success_file_path
        broadcast_response['terminate']['message'] = successful_message
        broadcast_response['result_json'] = json.dumps(result_json)
        await websocket_manager.broadcast(broadcast_response, channel_id)

    async def __broadcast_max_retry_error(self, channel_id, question_key, user_response):

        error_message = (user_response.get('max_retry_error') + " " +
                         InstantOffer.Messages.MAX_RETRY_MESSAGE.format(question_key=question_key))
        error_msg_path = await self.openai.text_to_speech(error_message, "error_message")
        error_msg_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", error_msg_path)

        broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
        broadcast_response['is_exiting'] = 'true'
        broadcast_response['error']['path'] = error_msg_path
        broadcast_response['error']['message'] = error_message
        await websocket_manager.broadcast(broadcast_response, channel_id)

    async def __handle_user_response(self, websocket, channel_id, question_key, question, user_response, result_json):
        """ This method is used to handle user raw input and prepares the final json result """

        user_response = await self.llm_response_handler.extract_and_validate(websocket, channel_id, question_key,
                                                                             question, user_response, result_json,
                                                                             retry_count=1)

        if not user_response.get('is_negation', ''):
            result_json = await self.llm_response_handler.update_result_json(result_json, user_response)
        else:
            result_json.update({'is_negation': True})

        return result_json

    async def get_response(self, websocket, channel_id):

        result_json = copy.deepcopy(InstantOffer.RESULT_JSON)
        initial_question = random.choice(InstantOffer.Messages.INITIAL)
        initial_file_path = await self.openai.text_to_speech(initial_question, "initial_question")
        initial_file_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", initial_file_path)

        for index, (question_key, question) in enumerate(InstantOffer.QUESTIONS.items()):
            if question_key == "successful_terminate":
                await self.__publish_successful_message(channel_id, result_json)
                break

            if question_key != "generic_question" and result_json[question_key] != "":
                continue

            question_text = random.choice(question)
            question_file_path = await self.openai.text_to_speech(question_text, question_key)
            question_file_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", question_file_path)

            broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
            broadcast_response['question']['path'] = question_file_path
            broadcast_response['question']['text'] = question_text

            if index == 0:
                broadcast_response['initial_message_path'] = initial_file_path

            await websocket_manager.broadcast(broadcast_response, channel_id)
            audio_data = await websocket.receive()
            mp3_data = await self.audio_handler.save_as_mp3(websocket, broadcast_response, question_key, audio_data,
                                                            channel_id)
            broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
            broadcast_response['user_response'] = mp3_data['user_response']
            await websocket_manager.broadcast(broadcast_response, channel_id)

            if isinstance(mp3_data['user_response'], dict):
                return

            user_response = await self.__handle_user_response(websocket, channel_id, question_key, question_text,
                                                              mp3_data['user_response'], result_json)

            if user_response.get('max_retry_error', ''):
                await self.__broadcast_max_retry_error(channel_id, question_key, user_response)
                break

            if user_response.get('is_negation', ''):
                break

            result_json = user_response
            broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
            broadcast_response['result_json'] = json.dumps(result_json)
            await websocket_manager.broadcast(broadcast_response, channel_id)
