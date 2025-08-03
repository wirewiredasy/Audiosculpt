"""
Audio Cutting Microservice
Handles audio segment extraction and trimming
"""
import os
import uuid
from pydub import AudioSegment
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AudioCuttingService:
    """Microservice for audio cutting and trimming"""
    
    async def cut_audio(self, input_path: str, output_dir: str, 
                       start_time: float, end_time: float) -> Dict[str, Any]:
        """Cut audio segment from start_time to end_time (in seconds)"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Convert to milliseconds
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            # Validate times
            if start_ms < 0 or end_ms > len(audio) or start_ms >= end_ms:
                return {'success': False, 'error': 'Invalid time range'}
            
            # Cut audio
            cut_audio = audio[start_ms:end_ms]
            
            output_filename = f"cut_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            cut_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Audio cut from {start_time}s to {end_time}s"
            }
            
        except Exception as e:
            logger.error(f"Error cutting audio: {e}")
            return {'success': False, 'error': f"Audio cutting failed: {str(e)}"}

    async def join_audio(self, input_paths: list, output_dir: str) -> Dict[str, Any]:
        """Join multiple audio files"""
        try:
            combined = AudioSegment.empty()
            
            for path in input_paths:
                if not os.path.exists(path):
                    return {'success': False, 'error': f'File not found: {path}'}
                audio = AudioSegment.from_file(path)
                combined += audio
            
            output_filename = f"joined_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            combined.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Successfully joined {len(input_paths)} audio files"
            }
            
        except Exception as e:
            logger.error(f"Error joining audio: {e}")
            return {'success': False, 'error': f"Audio joining failed: {str(e)}"}