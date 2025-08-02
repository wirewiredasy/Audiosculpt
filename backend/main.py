"""
FastAPI API Gateway for Audio Processing Microservices
"""
import os
import uuid
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import httpx

from backend.services.audio_processor import AudioProcessorService
from backend.models.schemas import (
    ProcessingRequest, 
    ProcessingResponse, 
    AudioInfo,
    VocalSeparationResponse
)

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)
os.makedirs("static", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    app.state.audio_service = AudioProcessorService()
    yield
    # Shutdown
    if hasattr(app.state, 'audio_service'):
        app.state.audio_service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="ODOREMOVER - Audio Processing API",
    description="Professional audio processing microservices with 11+ features",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    async with aiofiles.open("templates/index.html", mode='r') as f:
        content = await f.read()
    return HTMLResponse(content=content)

@app.post("/api/upload", response_model=AudioInfo)
async def upload_audio(file: UploadFile = File(...)):
    """Upload and validate audio file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file extension
    allowed_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"uploads/{unique_filename}"
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Get audio info
    audio_info = await app.state.audio_service.get_audio_info(file_path)
    audio_info.file_id = unique_filename
    audio_info.original_name = file.filename
    
    return audio_info

@app.post("/api/process/vocal-separation", response_model=VocalSeparationResponse)
async def separate_vocals(request: ProcessingRequest):
    """Separate vocals from instrumental"""
    file_path = f"uploads/{request.file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.separate_vocals(file_path)
    return result

@app.post("/api/process/pitch-tempo", response_model=ProcessingResponse)
async def adjust_pitch_tempo(
    file_id: str = Form(...),
    pitch_shift: float = Form(0),
    tempo_change: float = Form(1.0)
):
    """Adjust pitch and tempo"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.change_pitch_tempo(
        file_path, pitch_shift, tempo_change
    )
    return result

@app.post("/api/process/convert", response_model=ProcessingResponse)
async def convert_format(
    file_id: str = Form(...),
    output_format: str = Form(...)
):
    """Convert audio format"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.convert_format(file_path, output_format)
    return result

@app.post("/api/process/cut", response_model=ProcessingResponse)
async def cut_audio(
    file_id: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...)
):
    """Cut audio segment"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.cut_audio(file_path, start_time, end_time)
    return result

@app.post("/api/process/noise-reduction", response_model=ProcessingResponse)
async def reduce_noise(
    file_id: str = Form(...),
    noise_factor: float = Form(0.5)
):
    """Reduce background noise"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.reduce_noise(file_path, noise_factor)
    return result

@app.post("/api/process/normalize", response_model=ProcessingResponse)
async def normalize_volume(
    file_id: str = Form(...),
    target_db: float = Form(-20.0)
):
    """Normalize audio volume"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.normalize_volume(file_path, target_db)
    return result

@app.post("/api/process/fade", response_model=ProcessingResponse)
async def apply_fade(
    file_id: str = Form(...),
    fade_in: float = Form(0),
    fade_out: float = Form(0)
):
    """Apply fade in/out effects"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.apply_fade(file_path, fade_in, fade_out)
    return result

@app.post("/api/process/reverse", response_model=ProcessingResponse)
async def reverse_audio(request: ProcessingRequest):
    """Reverse audio playback"""
    file_path = f"uploads/{request.file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.reverse_audio(file_path)
    return result

@app.post("/api/process/equalizer", response_model=ProcessingResponse)
async def apply_equalizer(
    file_id: str = Form(...),
    low_gain: float = Form(0),
    mid_gain: float = Form(0),
    high_gain: float = Form(0)
):
    """Apply 3-band equalizer"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await app.state.audio_service.apply_equalizer(
        file_path, low_gain, mid_gain, high_gain
    )
    return result

@app.post("/api/process/metadata", response_model=ProcessingResponse)
async def edit_metadata(
    file_id: str = Form(...),
    title: Optional[str] = Form(None),
    artist: Optional[str] = Form(None),
    album: Optional[str] = Form(None),
    album_artist: Optional[str] = Form(None)
):
    """Edit MP3 metadata"""
    file_path = f"uploads/{file_id}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.lower().endswith('.mp3'):
        raise HTTPException(
            status_code=400, 
            detail="Metadata editing only supported for MP3 files"
        )
    
    metadata = {}
    if title: metadata['title'] = title
    if artist: metadata['artist'] = artist
    if album: metadata['album'] = album
    if album_artist: metadata['albumartist'] = album_artist
    
    result = await app.state.audio_service.edit_metadata(file_path, metadata)
    return result

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download processed file"""
    file_path = f"processed/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path, 
        media_type='application/octet-stream',
        filename=filename
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ODOREMOVER Audio Processing API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        log_level="info"
    )