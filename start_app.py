#!/usr/bin/env python3
"""
Audio Processor Pro - Production Server Startup Script
Properly configured for FastAPI with uvicorn
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Audio Processor Pro - FastAPI Application")
    print("📊 Features: Professional audio processing with microservices")
    print("🔗 Server will be available at: http://0.0.0.0:5000")
    print("📚 API docs will be at: http://0.0.0.0:5000/docs")
    print("-" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )