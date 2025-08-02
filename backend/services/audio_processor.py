"""
Audio Processing Service - Microservice for all audio operations
"""
import os
import uuid
import asyncio
import tempfile
import shutil
import logging
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2
from scipy import signal

from backend.models.schemas import (
    AudioInfo, ProcessingResponse, VocalSeparationResponse
)

logger = logging.getLogger(__name__)

class AudioProcessorService:
    """Microservice for audio processing operations"""
    
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def cleanup(self):
        """Clean up resources"""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")
        
        self.executor.shutdown(wait=True)
    
    def _validate_audio_file(self, file_path: str) -> bool:
        """Validate if file is a supported audio format"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                return False
            
            # Try to load with pydub
            AudioSegment.from_file(file_path)
            return True
        except Exception as e:
            logger.error(f"Invalid audio file {file_path}: {e}")
            return False
    
    async def get_audio_info(self, file_path: str) -> AudioInfo:
        """Get audio file information"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._get_audio_info_sync, file_path)
    
    def _get_audio_info_sync(self, file_path: str) -> AudioInfo:
        """Synchronous audio info extraction"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            info = AudioInfo(
                duration=len(audio) / 1000.0,  # seconds
                channels=audio.channels,
                frame_rate=audio.frame_rate,
                sample_width=audio.sample_width,
                bitrate=getattr(audio, 'bitrate', 'Unknown'),
                format=os.path.splitext(file_path)[1][1:].upper()
            )
            
            # Try to get metadata for MP3 files
            if file_path.lower().endswith('.mp3'):
                try:
                    mp3_file = MP3(file_path)
                    if mp3_file.tags:
                        info.title = str(mp3_file.tags.get('TIT2', ['Unknown'])[0])
                        info.artist = str(mp3_file.tags.get('TPE1', ['Unknown'])[0])
                        info.album = str(mp3_file.tags.get('TALB', ['Unknown'])[0])
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            raise
    
    async def separate_vocals(self, input_path: str) -> VocalSeparationResponse:
        """Separate vocals using center channel extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._separate_vocals_sync, input_path)
    
    def _separate_vocals_sync(self, input_path: str) -> VocalSeparationResponse:
        """Synchronous vocal separation"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Convert to numpy array for processing
            samples = np.array(audio.get_array_of_samples())
            
            if audio.channels == 2:
                # Reshape for stereo
                samples = samples.reshape((-1, 2))
                
                # Simple vocal removal: subtract center channel
                vocals = (samples[:, 0] + samples[:, 1]) / 2  # Center channel (vocals)
                instrumental = (samples[:, 0] - samples[:, 1]) / 2  # Side channels
                
                # Convert back to AudioSegment
                vocals_audio = AudioSegment(
                    vocals.astype(np.int16).tobytes(),
                    frame_rate=audio.frame_rate,
                    sample_width=audio.sample_width,
                    channels=1
                )
                
                instrumental_audio = AudioSegment(
                    instrumental.astype(np.int16).tobytes(),
                    frame_rate=audio.frame_rate,
                    sample_width=audio.sample_width,
                    channels=1
                )
            else:
                # Mono audio - can't separate effectively
                vocals_audio = audio
                instrumental_audio = AudioSegment.silent(duration=len(audio))
            
            # Save separated tracks
            vocals_filename = f"vocals_{uuid.uuid4()}.wav"
            instrumental_filename = f"instrumental_{uuid.uuid4()}.wav"
            
            vocals_path = f"processed/{vocals_filename}"
            instrumental_path = f"processed/{instrumental_filename}"
            
            vocals_audio.export(vocals_path, format='wav')
            instrumental_audio.export(instrumental_path, format='wav')
            
            return VocalSeparationResponse(
                success=True,
                vocals_file=vocals_filename,
                instrumental_file=instrumental_filename,
                message="Vocal separation completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in vocal separation: {e}")
            return VocalSeparationResponse(
                success=False,
                error=f"Vocal separation failed: {str(e)}"
            )
    
    async def change_pitch_tempo(self, input_path: str, pitch_shift: float = 0, 
                                tempo_change: float = 1.0) -> ProcessingResponse:
        """Change pitch and tempo using librosa"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._change_pitch_tempo_sync, 
            input_path, pitch_shift, tempo_change
        )
    
    def _change_pitch_tempo_sync(self, input_path: str, pitch_shift: float, 
                                tempo_change: float) -> ProcessingResponse:
        """Synchronous pitch/tempo change"""
        try:
            # Load audio with librosa
            y, sr = librosa.load(input_path, sr=None)
            
            # Apply pitch shift
            if pitch_shift != 0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)
            
            # Apply tempo change
            if tempo_change != 1.0:
                y = librosa.effects.time_stretch(y, rate=tempo_change)
            
            # Save the result
            output_filename = f"pitch_tempo_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            sf.write(output_path, y, sr)
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message="Pitch and tempo adjustment completed"
            )
            
        except Exception as e:
            logger.error(f"Error in pitch/tempo change: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Pitch/tempo change failed: {str(e)}"
            )
    
    async def convert_format(self, input_path: str, output_format: str) -> ProcessingResponse:
        """Convert audio to different format"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._convert_format_sync, input_path, output_format
        )
    
    def _convert_format_sync(self, input_path: str, output_format: str) -> ProcessingResponse:
        """Synchronous format conversion"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Set quality parameters based on format
            export_params = {}
            if output_format.lower() == 'mp3':
                export_params = {'bitrate': '320k'}
            elif output_format.lower() == 'ogg':
                export_params = {'codec': 'libvorbis'}
            
            output_filename = f"converted_{uuid.uuid4()}.{output_format}"
            output_path = f"processed/{output_filename}"
            
            audio.export(output_path, format=output_format.lower(), **export_params)
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message=f"Converted to {output_format.upper()} format"
            )
            
        except Exception as e:
            logger.error(f"Error in format conversion: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Format conversion failed: {str(e)}"
            )
    
    async def cut_audio(self, input_path: str, start_time: float, 
                       end_time: float) -> ProcessingResponse:
        """Cut audio segment"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._cut_audio_sync, input_path, start_time, end_time
        )
    
    def _cut_audio_sync(self, input_path: str, start_time: float, 
                       end_time: float) -> ProcessingResponse:
        """Synchronous audio cutting"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            cut_audio = audio[start_ms:end_ms]
            
            output_filename = f"cut_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            cut_audio.export(output_path, format='wav')
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message=f"Audio cut from {start_time}s to {end_time}s"
            )
            
        except Exception as e:
            logger.error(f"Error cutting audio: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Audio cutting failed: {str(e)}"
            )
    
    async def reduce_noise(self, input_path: str, 
                          noise_factor: float = 0.5) -> ProcessingResponse:
        """Reduce noise using spectral gating"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._reduce_noise_sync, input_path, noise_factor
        )
    
    def _reduce_noise_sync(self, input_path: str, noise_factor: float) -> ProcessingResponse:
        """Synchronous noise reduction"""
        try:
            # Load audio
            y, sr = librosa.load(input_path, sr=None)
            
            # Simple spectral gating using librosa
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            
            # Apply noise gate based on magnitude threshold
            threshold = np.percentile(magnitude, 20 * (1 - noise_factor))
            mask = magnitude > threshold
            
            # Apply the mask
            stft_filtered = stft * mask
            reduced_noise = librosa.istft(stft_filtered)
            
            # Save result
            output_filename = f"denoised_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            sf.write(output_path, reduced_noise, sr)
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message="Noise reduction completed"
            )
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Noise reduction failed: {str(e)}"
            )
    
    async def normalize_volume(self, input_path: str, 
                              target_dBFS: float = -20.0) -> ProcessingResponse:
        """Normalize audio volume"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._normalize_volume_sync, input_path, target_dBFS
        )
    
    def _normalize_volume_sync(self, input_path: str, target_dBFS: float) -> ProcessingResponse:
        """Synchronous volume normalization"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Normalize to target dBFS
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            output_filename = f"normalized_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            normalized_audio.export(output_path, format='wav')
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message=f"Volume normalized to {target_dBFS}dB"
            )
            
        except Exception as e:
            logger.error(f"Error normalizing volume: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Volume normalization failed: {str(e)}"
            )
    
    async def apply_fade(self, input_path: str, fade_in_duration: float = 0, 
                        fade_out_duration: float = 0) -> ProcessingResponse:
        """Apply fade in/out effects"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._apply_fade_sync, 
            input_path, fade_in_duration, fade_out_duration
        )
    
    def _apply_fade_sync(self, input_path: str, fade_in_duration: float, 
                        fade_out_duration: float) -> ProcessingResponse:
        """Synchronous fade application"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            if fade_in_duration > 0:
                audio = audio.fade_in(int(fade_in_duration * 1000))
            
            if fade_out_duration > 0:
                audio = audio.fade_out(int(fade_out_duration * 1000))
            
            output_filename = f"faded_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            audio.export(output_path, format='wav')
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message="Fade effects applied successfully"
            )
            
        except Exception as e:
            logger.error(f"Error applying fade: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Fade application failed: {str(e)}"
            )
    
    async def reverse_audio(self, input_path: str) -> ProcessingResponse:
        """Reverse audio playback"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._reverse_audio_sync, input_path)
    
    def _reverse_audio_sync(self, input_path: str) -> ProcessingResponse:
        """Synchronous audio reversal"""
        try:
            audio = AudioSegment.from_file(input_path)
            reversed_audio = audio.reverse()
            
            output_filename = f"reversed_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            reversed_audio.export(output_path, format='wav')
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message="Audio reversed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error reversing audio: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Audio reversal failed: {str(e)}"
            )
    
    async def apply_equalizer(self, input_path: str, low_gain: float = 0, 
                             mid_gain: float = 0, high_gain: float = 0) -> ProcessingResponse:
        """Apply 3-band equalizer"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._apply_equalizer_sync, 
            input_path, low_gain, mid_gain, high_gain
        )
    
    def _apply_equalizer_sync(self, input_path: str, low_gain: float, 
                             mid_gain: float, high_gain: float) -> ProcessingResponse:
        """Synchronous equalizer application"""
        try:
            # Load audio
            y, sr = librosa.load(input_path, sr=None)
            
            # Define frequency bands
            low_freq = 300   # Hz
            high_freq = 3000 # Hz
            
            # Create filters
            nyquist = sr / 2
            
            # Low band (below 300 Hz)
            if low_gain != 0:
                low_sos = signal.butter(4, low_freq / nyquist, btype='low', output='sos')
                low_filtered = signal.sosfilt(low_sos, y)
                low_filtered *= (10 ** (low_gain / 20))
                y = y + (low_filtered - signal.sosfilt(low_sos, y))
            
            # High band (above 3000 Hz)
            if high_gain != 0:
                high_sos = signal.butter(4, high_freq / nyquist, btype='high', output='sos')
                high_filtered = signal.sosfilt(high_sos, y)
                high_filtered *= (10 ** (high_gain / 20))
                y = y + (high_filtered - signal.sosfilt(high_sos, y))
            
            # Mid band (300-3000 Hz)
            if mid_gain != 0:
                mid_sos = signal.butter(4, [low_freq / nyquist, high_freq / nyquist], 
                                      btype='band', output='sos')
                mid_filtered = signal.sosfilt(mid_sos, y)
                mid_filtered *= (10 ** (mid_gain / 20))
                y = y + (mid_filtered - signal.sosfilt(mid_sos, y))
            
            # Normalize to prevent clipping
            y = y / np.max(np.abs(y))
            
            # Save result
            output_filename = f"equalized_{uuid.uuid4()}.wav"
            output_path = f"processed/{output_filename}"
            sf.write(output_path, y, sr)
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message="Equalizer applied successfully"
            )
            
        except Exception as e:
            logger.error(f"Error applying equalizer: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Equalizer application failed: {str(e)}"
            )
    
    async def edit_metadata(self, input_path: str, metadata: Dict[str, str]) -> ProcessingResponse:
        """Edit MP3 metadata"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._edit_metadata_sync, input_path, metadata
        )
    
    def _edit_metadata_sync(self, input_path: str, metadata: Dict[str, str]) -> ProcessingResponse:
        """Synchronous metadata editing"""
        try:
            output_filename = f"metadata_{uuid.uuid4()}.mp3"
            output_path = f"processed/{output_filename}"
            
            # Copy file first
            shutil.copy2(input_path, output_path)
            
            # Load and edit metadata
            audio_file = MP3(output_path, ID3=ID3)
            
            # Add ID3 tag if it doesn't exist
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # Set metadata fields
            if 'title' in metadata:
                audio_file.tags.add(TIT2(encoding=3, text=metadata['title']))
            if 'artist' in metadata:
                audio_file.tags.add(TPE1(encoding=3, text=metadata['artist']))
            if 'album' in metadata:
                audio_file.tags.add(TALB(encoding=3, text=metadata['album']))
            if 'albumartist' in metadata:
                audio_file.tags.add(TPE2(encoding=3, text=metadata['albumartist']))
            
            audio_file.save()
            
            return ProcessingResponse(
                success=True,
                processed_file=output_filename,
                message="Metadata updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Error editing metadata: {e}")
            return ProcessingResponse(
                success=False,
                error=f"Metadata editing failed: {str(e)}"
            )