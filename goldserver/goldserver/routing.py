# In routing.py
from channels.routing import route
from gold_admin.consumers import *
channel_routing = [
    #route("http.request", "gold_admin.consumers.http_consumer"),
    #route("websocket.receive", ws_message),
    route("websocket.connect", ws_add),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
]
