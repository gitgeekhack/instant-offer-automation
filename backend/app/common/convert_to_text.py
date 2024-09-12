import os

from openai import OpenAI

openai_api_key = os.getenv('OPENAI_API_KEY', "sk-my-service-account-x8qobWZdT6FtsGshjGPJT3BlbkFJSQdEDj2sZSrDdSDPZ6Vw")
openai_client = OpenAI(api_key=openai_api_key)

full_path = "/home/vivek/Downloads/Over the Calls/2022.07.12 09_18 - 10550292 - In - Antwon Townsend - 17163166627 - 251s.mp3"
user_response = ""
with open(full_path, "rb") as audio_file:
    transcription = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language="en"
    )
    user_response = str(transcription)

with open('/home/vivek/Desktop/2022.07.12 09_18 - 10550292 - In - Antwon Townsend - 17163166627 - 251s.txt', "w") as fp:
    fp.write(user_response)

