from langchain_core.callbacks.base import AsyncCallbackHandler

import json


class WebSocketCallbackHandler(AsyncCallbackHandler):
    def __init__(self, websocket, user, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.websocket = websocket

    async def on_llm_new_token(self, txt, **kwargs):
        msg = {
            'generated_token': txt, 
            'token': self.user,
            'type': 'NEW_TOKEN'
        }
        await self.websocket.send(json.dumps(msg))
