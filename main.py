"""
Audio Processor Pro - FastAPI Microservices Gateway
Entry point for the audio processing application - WSGI/ASGI compatible
"""
import asyncio
from threading import Thread
import sys
from backend.main import app as fastapi_app

class ASGIToWSGIAdapter:
    """Convert ASGI app to WSGI compatible for gunicorn"""
    
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app
    
    def __call__(self, environ, start_response):
        """WSGI application interface"""
        # Create a new event loop for this thread if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Convert WSGI to ASGI scope
        scope = {
            "type": "http",
            "method": environ["REQUEST_METHOD"],
            "path": environ.get("PATH_INFO", "/"),
            "query_string": environ.get("QUERY_STRING", "").encode(),
            "headers": [(k.lower().encode(), v.encode()) for k, v in 
                       [(key[5:].replace("_", "-"), value) for key, value in environ.items() 
                        if key.startswith("HTTP_")] + 
                       [("content-type", environ.get("CONTENT_TYPE", "")),
                        ("content-length", environ.get("CONTENT_LENGTH", ""))]
                       if v],
            "server": (environ.get("SERVER_NAME", "localhost"), 
                      int(environ.get("SERVER_PORT", "5000"))),
        }
        
        # Response data
        response_data = {"status": 500, "headers": [], "body": b""}
        
        async def receive():
            # Read request body if present
            try:
                content_length = int(environ.get("CONTENT_LENGTH", "0"))
                if content_length > 0:
                    body = environ["wsgi.input"].read(content_length)
                else:
                    body = b""
            except:
                body = b""
            
            return {"type": "http.request", "body": body}
        
        async def send(message):
            if message["type"] == "http.response.start":
                response_data["status"] = message["status"]
                response_data["headers"] = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_data["body"] += message.get("body", b"")
        
        # Run the ASGI app
        try:
            loop.run_until_complete(self.asgi_app(scope, receive, send))
        except Exception as e:
            # Return error response
            response_data["status"] = 500
            response_data["body"] = f"Internal Server Error: {str(e)}".encode()
        
        # Convert headers back to WSGI format
        headers = [(h[0].decode() if isinstance(h[0], bytes) else h[0], 
                   h[1].decode() if isinstance(h[1], bytes) else h[1]) 
                  for h in response_data["headers"]]
        
        # Start the response
        status_line = f"{response_data['status']} {self._get_status_text(response_data['status'])}"
        start_response(status_line, headers)
        
        return [response_data["body"]]
    
    def _get_status_text(self, status_code):
        """Get status text for HTTP status code"""
        status_texts = {
            200: "OK", 404: "Not Found", 500: "Internal Server Error",
            400: "Bad Request", 405: "Method Not Allowed"
        }
        return status_texts.get(status_code, "Unknown")

# Create WSGI-compatible app for gunicorn
app = ASGIToWSGIAdapter(fastapi_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        log_level="info"
    )