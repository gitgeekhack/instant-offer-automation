import os
from openai import OpenAI
from dotenv import load_dotenv

from app.constants import InstantOffer

load_dotenv()

os.makedirs(InstantOffer.VOICE_NOTE_PATH, exist_ok=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=openai_api_key)
