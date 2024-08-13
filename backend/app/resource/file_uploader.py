import os
from fastapi import UploadFile, File

from app import app
from app.constants import InstantOffer


@app.post("/upload")
async def upload_file(file: UploadFile = File()):
    file_location = os.path.join(InstantOffer.VOICE_NOTE_PATH, file.filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}
