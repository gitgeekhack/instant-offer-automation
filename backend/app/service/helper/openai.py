import os
import time
import random

from app.common.utils import logger
from app.service import openai_client
from app.constants import InstantOffer


class OpenAI:
    def __init__(self):
        self.openai_client = openai_client
        self.voice = random.choice(InstantOffer.AGENT_VOICES)

    async def text_to_speech(self, text, name, path=InstantOffer.VOICE_NOTE_PATH):
        x = time.time()
        response = self.openai_client.audio.speech.create(model="tts-1", input=text, voice=self.voice,
                                                          response_format="mp3")
        file_name = f"{name}.mp3"
        file_path = os.path.join(path, file_name)
        response.stream_to_file(file_path)
        logger.info(f"[Execution Time] Text to Speech for {name} is completed in: {time.time() - x} seconds.")
        return file_name

    async def invoke_gpt4o(self, prompt, user_response):
        x = time.time()

        completion = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_response}
            ]
        )
        response = completion.choices[0].message.content

        logger.info(f"[Execution Time] GPT4o generates response in: {time.time() - x} seconds.")

        return response
