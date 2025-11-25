class WebSocketManager:
    def __init__(self):
        self.connections = set()
        self.loop = None
        
    async def register(self, websocket):
        self.connections.add(websocket)
        print("[WebSocketManager] New connection registered")

    async def unregister(self, websocket):
        self.connections.remove(websocket)
        print("[WebSocketManager] Connection removed")

    async def broadcast(self, message):
        to_remove = set()
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"[WebSocketManager] Failed to send message: {e}")
                to_remove.add(ws)
        
        self.connections -= to_remove  # Remove broken connections
