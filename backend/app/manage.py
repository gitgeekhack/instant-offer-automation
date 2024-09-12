from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.constants import InstantOffer
from app.common.utils import get_logger


def create_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/instant-offer-automation-backend/uploads", StaticFiles(directory=InstantOffer.VOICE_NOTE_PATH),
              name="uploads")
    logger = get_logger()
    logger.info("FastAPI Server Started...")
    return app, logger
