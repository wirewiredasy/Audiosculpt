"""
Volume Normalization Microservice
Handles audio volume adjustment and normalization
"""
import os
import uuid
from pydub import AudioSegment
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class VolumeNormalizationService:
    """Microservice for volume normalization"""
    
    async def normalize_volume(self, input_path: str, output_dir: str, 
                              target_dBFS: float = -20.0) -> Dict[str, Any]:
        """Normalize audio volume to target dBFS"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Calculate the change needed
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            output_filename = f"normalized_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            normalized_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Volume normalized to {target_dBFS} dBFS"
            }
            
        except Exception as e:
            logger.error(f"Error normalizing volume: {e}")
            return {'success': False, 'error': f"Volume normalization failed: {str(e)}"}

    async def adjust_volume(self, input_path: str, output_dir: str, 
                           volume_change_db: float) -> Dict[str, Any]:
        """Adjust volume by specific dB amount"""
        try:
            audio = AudioSegment.from_file(input_path)
            adjusted_audio = audio.apply_gain(volume_change_db)
            
            output_filename = f"volume_adjusted_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            adjusted_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Volume adjusted by {volume_change_db:+.1f} dB"
            }
            
        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            return {'success': False, 'error': f"Volume adjustment failed: {str(e)}"}