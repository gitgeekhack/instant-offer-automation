from fastapi import WebSocket

from app.manage import create_app
from app.resource.instant_offer_generation import InstantOfferGenerator

app, logger = create_app()


@app.websocket("/ws/{channel_id}")
async def websocket_route(websocket: WebSocket, channel_id: str):
    instant_offer_generator = InstantOfferGenerator()
    await instant_offer_generator.handle_socket_connection(websocket, channel_id)
