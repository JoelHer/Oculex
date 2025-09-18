import asyncio
from backend.backendServer import HttpServer

if __name__ == "__main__":
    import uvicorn
    config = uvicorn.Config(HttpServer, host="0.0.0.0", port=5000, reload=False)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())  # Use asyncio.run() instead of get_event_loop()
