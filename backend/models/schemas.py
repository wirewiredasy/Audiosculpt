"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProcessingRequest(BaseModel):
    file_id: str

class ProcessingResponse(BaseModel):
    success: bool
    processed_file: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class VocalSeparationResponse(BaseModel):
    success: bool
    vocals_file: Optional[str] = None
    instrumental_file: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class AudioInfo(BaseModel):
    file_id: Optional[str] = None
    original_name: Optional[str] = None
    duration: float
    channels: int
    frame_rate: int
    sample_width: int
    format: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    bitrate: Optional[str] = None

class MetadataRequest(BaseModel):
    file_id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    album_artist: Optional[str] = None

class PitchTempoRequest(BaseModel):
    file_id: str
    pitch_shift: float = 0
    tempo_change: float = 1.0

class NoiseReductionRequest(BaseModel):
    file_id: str
    noise_factor: float = 0.5

class EqualizerRequest(BaseModel):
    file_id: str
    low_gain: float = 0
    mid_gain: float = 0
    high_gain: float = 0

class FadeRequest(BaseModel):
    file_id: str
    fade_in: float = 0
    fade_out: float = 0

class CutRequest(BaseModel):
    file_id: str
    start_time: float
    end_time: float

class ConvertRequest(BaseModel):
    file_id: str
    output_format: str