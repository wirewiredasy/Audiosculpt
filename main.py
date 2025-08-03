"""
Audio Processor Pro - FastAPI Microservices Gateway
Entry point for the audio processing application
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5000, reload=True)
else:
    from backend.main import app