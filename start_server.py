#!/usr/bin/env python3
"""
Audio Processor Pro - Server Startup Script
Run this to start the FastAPI microservices application
"""
import os
import sys
import uvicorn

def main():
    """Start the FastAPI application with uvicorn"""
    print("🚀 Starting Audio Processor Pro - FastAPI Microservices")
    print("📊 Features: 13 audio processing endpoints across 8 microservices")
    print("🔗 Server will be available at: http://localhost:5000")
    print("📚 API docs will be at: http://localhost:5000/docs")
    print("-" * 60)
    
    try:
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()