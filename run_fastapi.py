#!/usr/bin/env python3
"""
Run FastAPI Application with uvicorn
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )