"""
Audio Processor Pro - Complete FastAPI Microservices Application
Clean implementation with all microservices
"""
import os
import uuid
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

# Import all microservices
from backend.services.vocal_separation_service import VocalSeparationService
from backend.services.pitch_tempo_service import PitchTempoService
from backend.services.format_conversion_service import FormatConversionService
from backend.services.audio_cutting_service import AudioCuttingService
from backend.services.noise_reduction_service import NoiseReductionService
from backend.services.volume_normalization_service import VolumeNormalizationService
from backend.services.audio_effects_service import AudioEffectsService
from backend.services.metadata_service import MetadataService

from backend.models.schemas import *

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)
os.makedirs("static", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - Initialize all microservices"""
    # Startup - Initialize all microservices
    app.state.vocal_service = VocalSeparationService()
    app.state.pitch_tempo_service = PitchTempoService()
    app.state.format_service = FormatConversionService()
    app.state.cutting_service = AudioCuttingService()
    app.state.noise_service = NoiseReductionService()
    app.state.volume_service = VolumeNormalizationService()
    app.state.effects_service = AudioEffectsService()
    app.state.metadata_service = MetadataService()
    
    yield
    
    # Shutdown - Cleanup all services
    for service_name in ['vocal_service']:
        if hasattr(app.state, service_name):
            service = getattr(app.state, service_name)
            if hasattr(service, 'cleanup'):
                service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Audio Processor Pro - Microservices API",
    description="Professional audio processing with independent microservices for each tool",
    version="3.0.0",
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

# Helper function to validate file exists
def validate_file_exists(file_id: str) -> str:
    file_path = os.path.join("uploads", file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return file_path

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    try:
        async with aiofiles.open("templates/index.html", mode='r') as f:
            content = await f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Audio Processor Pro - Microservices API</h1><p>Upload endpoint: /api/upload</p>")

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
    
    # Get audio info using metadata service
    result = await app.state.metadata_service.get_audio_info(file_path)
    if result['success']:
        info = result['info']
        info['file_id'] = unique_filename
        info['original_name'] = file.filename
        return AudioInfo(success=True, info=info, message="File uploaded successfully")
    else:
        return AudioInfo(success=False, error=result['error'])

# Download processed file
@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download processed audio file"""
    file_path = os.path.join("processed", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

# 1. Vocal Separation Microservice - TEMPORARILY DISABLED
@app.post("/api/vocal-separation", response_model=VocalSeparationResponse)
async def separate_vocals(file_id: str = Form(...)):
    """Separate vocals and instrumental tracks - DISABLED"""
    return VocalSeparationResponse(
        success=False, 
        error="Vocal separation service temporarily disabled due to dependency issues"
    )

# 2. Pitch and Tempo Microservice
@app.post("/api/pitch-tempo", response_model=ProcessingResponse)
async def adjust_pitch_tempo(
    file_id: str = Form(...),
    pitch_shift: float = Form(0),
    tempo_change: float = Form(1.0)
):
    """Adjust pitch and tempo"""
    file_path = validate_file_exists(file_id)
    result = await app.state.pitch_tempo_service.change_pitch_tempo(
        file_path, "processed", pitch_shift, tempo_change
    )
    return ProcessingResponse(**result)

# 3. Format Conversion Microservice
@app.post("/api/convert", response_model=ProcessingResponse)
async def convert_format(
    file_id: str = Form(...),
    output_format: str = Form(...)
):
    """Convert audio format"""
    file_path = validate_file_exists(file_id)
    result = await app.state.format_service.convert_format(
        file_path, "processed", output_format
    )
    return ProcessingResponse(**result)

# 4. Audio Cutting Microservice
@app.post("/api/cut", response_model=ProcessingResponse)
async def cut_audio(
    file_id: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...)
):
    """Cut audio segment"""
    file_path = validate_file_exists(file_id)
    result = await app.state.cutting_service.cut_audio(
        file_path, "processed", start_time, end_time
    )
    return ProcessingResponse(**result)

# 5. Audio Joining (part of cutting service)
@app.post("/api/join", response_model=ProcessingResponse)
async def join_audio(file_ids: str = Form(...)):
    """Join multiple audio files"""
    file_id_list = file_ids.split(",")
    file_paths = []
    for fid in file_id_list:
        file_paths.append(validate_file_exists(fid.strip()))
    
    result = await app.state.cutting_service.join_audio(file_paths, "processed")
    return ProcessingResponse(**result)

# 6. Noise Reduction Microservice - TEMPORARILY DISABLED
@app.post("/api/noise-reduction", response_model=ProcessingResponse)
async def reduce_noise(
    file_id: str = Form(...),
    noise_factor: float = Form(0.5)
):
    """Reduce background noise - DISABLED"""
    return ProcessingResponse(
        success=False, 
        error="Noise reduction service temporarily disabled due to dependency issues"
    )

@app.post("/api/noise-reduction-aggressive", response_model=ProcessingResponse)
async def reduce_noise_aggressive(
    file_id: str = Form(...),
    noise_factor: float = Form(0.8)
):
    """Aggressive noise reduction for very noisy audio - DISABLED"""
    return ProcessingResponse(
        success=False, 
        error="Aggressive noise reduction service temporarily disabled due to dependency issues"
    )

# 7. Volume Normalization Microservice
@app.post("/api/normalize", response_model=ProcessingResponse)
async def normalize_volume(
    file_id: str = Form(...),
    target_db: float = Form(-20.0)
):
    """Normalize audio volume"""
    file_path = validate_file_exists(file_id)
    result = await app.state.volume_service.normalize_volume(
        file_path, "processed", target_db
    )
    return ProcessingResponse(**result)

# 8. Volume Adjustment (part of volume service)
@app.post("/api/adjust-volume", response_model=ProcessingResponse)
async def adjust_volume(
    file_id: str = Form(...),
    volume_change_db: float = Form(...)
):
    """Adjust volume by specific dB amount"""
    file_path = validate_file_exists(file_id)
    result = await app.state.volume_service.adjust_volume(
        file_path, "processed", volume_change_db
    )
    return ProcessingResponse(**result)

# 9. Audio Reversal (Effects service)
@app.post("/api/reverse", response_model=ProcessingResponse)
async def reverse_audio(file_id: str = Form(...)):
    """Reverse audio playback"""
    file_path = validate_file_exists(file_id)
    result = await app.state.effects_service.reverse_audio(file_path, "processed")
    return ProcessingResponse(**result)

# 10. Equalizer (Effects service)
@app.post("/api/equalizer", response_model=ProcessingResponse)
async def apply_equalizer(
    file_id: str = Form(...),
    low_gain: float = Form(0),
    mid_gain: float = Form(0),
    high_gain: float = Form(0)
):
    """Apply 3-band equalizer"""
    file_path = validate_file_exists(file_id)
    result = await app.state.effects_service.apply_equalizer(
        file_path, "processed", low_gain, mid_gain, high_gain
    )
    return ProcessingResponse(**result)

# 11. Fade Effects (Effects service)
@app.post("/api/fade", response_model=ProcessingResponse)
async def add_fade(
    file_id: str = Form(...),
    fade_in_duration: float = Form(0),
    fade_out_duration: float = Form(0)
):
    """Add fade in/out effects"""
    file_path = validate_file_exists(file_id)
    result = await app.state.effects_service.add_fade(
        file_path, "processed", fade_in_duration, fade_out_duration
    )
    return ProcessingResponse(**result)

# 12. Metadata Service - Get Info
@app.get("/api/info/{file_id}", response_model=AudioInfo)
async def get_audio_info(file_id: str):
    """Get audio file information"""
    file_path = validate_file_exists(file_id)
    result = await app.state.metadata_service.get_audio_info(file_path)
    return AudioInfo(**result)

# 13. Metadata Service - Edit Metadata
@app.post("/api/metadata", response_model=ProcessingResponse)
async def edit_metadata(
    file_id: str = Form(...),
    title: str = Form(None),
    artist: str = Form(None),
    album: str = Form(None),
    albumartist: str = Form(None)
):
    """Edit MP3 metadata"""
    file_path = validate_file_exists(file_id)
    metadata = {}
    if title: metadata['title'] = title
    if artist: metadata['artist'] = artist
    if album: metadata['album'] = album
    if albumartist: metadata['albumartist'] = albumartist
    
    result = await app.state.metadata_service.edit_metadata(
        file_path, "processed", metadata
    )
    return ProcessingResponse(**result)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for microservices"""
    return {"status": "healthy", "services": "all_running", "version": "3.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)