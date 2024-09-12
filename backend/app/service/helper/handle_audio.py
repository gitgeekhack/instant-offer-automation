import io
import os
import time
from pydub import AudioSegment
import speech_recognition as sr

from app.common.utils import logger
from app.constants import InstantOffer
from app.common.web_socket_utils import websocket_manager


class AudioHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    async def save_as_mp3(self, websocket, broadcast_response, name, audio_data, channel_id, path=InstantOffer.VOICE_NOTE_PATH):
        """ This method is used to save recorded audio as MP3 in a specified folder """

        x = time.time()
        error_message = None
        with io.BytesIO(audio_data['bytes']) as fio:
            fio.seek(0)
            with sr.AudioFile(fio) as source:
                audio_data = self.recognizer.record(source)

        full_path, user_response = None, None
        try:
            file_name = f'response_{name}.wav'
            full_path = os.path.join(path, channel_id, file_name)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data.get_wav_data()))
            audio_segment.export(full_path, format='mp3')
            user_response = self.recognizer.recognize_google(audio_data)
            logger.info(f"User Response: {user_response}")

        except sr.UnknownValueError:
            error_message = {"error_message": "Speech not recognized. Please try again."}
            await websocket_manager.broadcast(broadcast_response, channel_id)
            audio_data = await websocket.receive()
            mp3_data = await self.save_as_mp3(websocket, broadcast_response, name, audio_data, channel_id)
            return mp3_data

        except sr.RequestError as e:
            error_message = {"error_message": f"Could not request results: {str(e)}"}

        logger.info(f"[Execution Time] Save MP3 file for {name} is completed in: {time.time() - x} seconds.")
        return {"file_path": full_path, "user_response": user_response, "error_message": error_message}
