import ast
import copy
import os.path
import traceback
from datetime import datetime

from app.common.utils import logger
from app.constants import InstantOffer
from app.service.helper.handle_audio import AudioHandler
from app.common.web_socket_utils import websocket_manager


class LLMResponseHandler:

    def __init__(self, openai):
        self.openai = openai
        self.audio_handler = AudioHandler(self.openai)

    async def update_result_json(self, result_json, llm_response):
        for key in result_json.keys():
            if llm_response[key] != "":
                result_json[key] = llm_response[key]

        logger.info(f"Current Response: {result_json}")
        return result_json

    async def convert_to_json(self, llm_response, print_message=False):

        final_json = copy.deepcopy(InstantOffer.RESULT_JSON)
        try:
            start = llm_response.index('{')
            end = llm_response.index('}') + 1
            llm_response = llm_response[start:end]
            llm_response = llm_response.replace("true", "True")
            llm_response = llm_response.replace("false", "False")
            final_json = ast.literal_eval(llm_response)

            if print_message:
                logger.info(f"LLM Response: {llm_response}")
        except Exception as e:
            logger.error(f"{e} -> {traceback.format_exc()}")

        return final_json

    async def handle_negation_response(self, channel_id, llm_response, question_key):
        """ This method is used to handle the negation in the user response """

        if llm_response.get('is_negation', ''):
            intermediate_terminate_message = InstantOffer.Messages.INTERMEDIATE_TERMINATE.format(question_key)
            message_path = await self.openai.text_to_speech(intermediate_terminate_message,
                                                            "intermediate_terminate_message")
            message_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", message_path)

            broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
            broadcast_response['intermediate_terminate']['path'] = message_path
            broadcast_response['intermediate_terminate']['message'] = intermediate_terminate_message
            logger.info(f"Agent: {intermediate_terminate_message}")
            await websocket_manager.broadcast(broadcast_response, channel_id)
            return True

        return False

    async def handle_error_response(self, websocket, channel_id, llm_response, question_key, question, result_json,
                                    retry_count):
        """ This method is used to handle the error in the user response """

        if llm_response.get('error_message', ''):
            if retry_count < InstantOffer.MAX_RETRY:

                error_msg = llm_response.get('error_message')
                error_file_path = await self.openai.text_to_speech(error_msg, f'error_{question_key}')
                error_file_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", error_file_path)
                logger.info(f"Agent: {error_msg}")

                broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
                broadcast_response['error']['path'] = error_file_path
                broadcast_response['error']['message'] = error_msg

                question_file_path = await self.openai.text_to_speech(question, question_key)
                logger.info(f"Agent: {question}")

                if question_key == 'generic_question':
                    await websocket_manager.broadcast(broadcast_response, channel_id)
                    return False

                question_file_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", question_file_path)
                broadcast_response['question']['path'] = question_file_path
                broadcast_response['question']['text'] = question
                await websocket_manager.broadcast(broadcast_response, channel_id)

                audio_data = await websocket.receive()
                mp3_data = await self.audio_handler.save_as_mp3(websocket, broadcast_response, question_key, audio_data,
                                                                channel_id)

                broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
                if mp3_data['error_message']:
                    error_message = mp3_data['error_message']
                    error_msg_path = await self.openai.text_to_speech(error_message, "error_message")
                    error_msg_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", error_msg_path)

                    broadcast_response['error']['path'] = error_msg_path
                    broadcast_response['error']['message'] = error_message

                broadcast_response['user_response'] = mp3_data['user_response']
                await websocket_manager.broadcast(broadcast_response, channel_id)

                return await self.extract_and_validate(websocket, channel_id, question_key, question,
                                                       mp3_data['user_response'], result_json, retry_count + 1)
            else:
                logger.info(InstantOffer.Messages.MAX_RETRY_MESSAGE.format(question_key=question_key))
                result_json.update({'max_retry_error': llm_response['error_message']})
                return result_json
        return False

    async def handle_missing_response(self, websocket, channel_id, llm_response, question_key, question, result_json,
                                      retry_count):
        """ This method is used to handle the missing values in result_json """

        result_json = await self.update_result_json(result_json, llm_response)

        if retry_count < InstantOffer.MAX_RETRY:
            re_ask_message = InstantOffer.Messages.RE_ASK_MESSAGE.format(question_key=question_key)
            re_ask_message_path = await self.openai.text_to_speech(re_ask_message, 're_ask_message')
            re_ask_message_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", re_ask_message_path)

            broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
            broadcast_response['question']['path'] = re_ask_message_path
            broadcast_response['question']['text'] = re_ask_message
            broadcast_response['result_json'] = result_json
            await websocket_manager.broadcast(broadcast_response, channel_id)

            audio_data = await websocket.receive()
            mp3_data = await self.audio_handler.save_as_mp3(websocket, broadcast_response, question_key, audio_data,
                                                            channel_id)

            broadcast_response = copy.deepcopy(InstantOffer.BROADCAST_MESSAGE)
            if mp3_data['error_message']:
                error_message = mp3_data['error_message']
                error_msg_path = await self.openai.text_to_speech(error_message, "error_message")
                error_msg_path = os.path.join(InstantOffer.VOICE_NOTE_URL, "uploads", error_msg_path)

                broadcast_response['error']['path'] = error_msg_path
                broadcast_response['error']['message'] = error_message

            broadcast_response['user_response'] = mp3_data['user_response']
            await websocket_manager.broadcast(broadcast_response, channel_id)

            return await self.extract_and_validate(websocket, channel_id, question_key, question,
                                                   mp3_data['user_response'], result_json, retry_count + 1)
        else:
            logger.info(InstantOffer.Messages.MAX_RETRY_MESSAGE.format(question_key=question_key))
            return None

    async def get_question_key_for_update(self, response):
        true_keys = [key for key, value in response.items() if value]
        return true_keys if true_keys else None

    async def extract_and_validate(self, websocket, channel_id, question_key, question, user_response, result_json,
                                   retry_count=1):
        """ This method is used to extract & validate the user response using ChatGPT-4o """

        mile_words = ['miles', 'mileage']

        if question_key == "mileage" and not any(x in user_response for x in mile_words):
            user_response = f"The mileage is {user_response}"

        if user_response is None:
            return None

        current_year = datetime.now().year

        if question_key == "mileage":
            prompt = InstantOffer.Prompt.MILEAGE_PROMPT.format(result_json=result_json)
        elif question_key == "postal_code":
            prompt = InstantOffer.Prompt.POSTAL_CODE_PROMPT.format(result_json=result_json)
        else:
            prompt = InstantOffer.Prompt.GENERIC_PROMPT.format(result_json=result_json,
                                                               current_year=current_year,
                                                               question_key=question_key)

        validated_response = await self.openai.invoke_gpt4o(prompt, user_response)
        llm_response = await self.convert_to_json(validated_response, print_message=True)

        if await self.handle_negation_response(channel_id, llm_response, question_key):
            result_json.update({'is_negation': True})
            return result_json

        error_response = await self.handle_error_response(websocket, channel_id, llm_response, question_key, question,
                                                          result_json, retry_count=retry_count)
        if error_response:
            return error_response

        if question_key != "generic_question" and not llm_response.get(question_key, ''):
            missing_response = await self.handle_missing_response(websocket, channel_id, llm_response, question_key,
                                                                  question, result_json, retry_count=retry_count)
            if missing_response:
                return missing_response

        return llm_response
