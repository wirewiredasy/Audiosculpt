"""
Audio Processor Pro - FastAPI Microservices Gateway
Entry point for the audio processing application - Dual compatible
"""
import asyncio
from backend.main import app as fastapi_app

class ASGItoWSGI:
    """Simple ASGI to WSGI adapter for gunicorn compatibility"""
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app
    
    def __call__(self, environ, start_response):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except:
            try:
                loop = asyncio.get_event_loop()
            except:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        
        scope = {
            "type": "http",
            "method": environ["REQUEST_METHOD"],
            "path": environ.get("PATH_INFO", "/"),
            "query_string": environ.get("QUERY_STRING", "").encode(),
            "headers": [],
        }
        
        response = {"status": 200, "headers": [], "body": b""}
        
        async def receive():
            return {"type": "http.request", "body": b""}
        
        async def send(message):
            if message["type"] == "http.response.start":
                response["status"] = message["status"]
                response["headers"] = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response["body"] += message.get("body", b"")
        
        try:
            loop.run_until_complete(self.asgi_app(scope, receive, send))
        except Exception as e:
            response["status"] = 500
            response["body"] = f"Internal Server Error: {str(e)}".encode()
        
        status_line = f"{response['status']} OK" if response['status'] == 200 else f"{response['status']} Error"
        headers = [(h[0].decode() if isinstance(h[0], bytes) else str(h[0]), 
                   h[1].decode() if isinstance(h[1], bytes) else str(h[1])) 
                  for h in response["headers"]]
        
        start_response(status_line, headers)
        return [response["body"]]

# Export for gunicorn
app = ASGItoWSGI(fastapi_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        log_level="info"
    )