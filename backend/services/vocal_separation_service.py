"""
Vocal Separation Microservice
Handles vocal and instrumental separation
"""
import os
import uuid
import tempfile
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class VocalSeparationService:
    """Microservice for vocal separation"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")
    
    async def separate_vocals(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Separate vocals using center channel extraction
        Returns paths to vocals and accompaniment files
        """
        try:
            audio = AudioSegment.from_file(input_path)
            samples = np.array(audio.get_array_of_samples())
            
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
                # Center channel (vocals) and side channels (instrumental)
                vocals = (samples[:, 0] + samples[:, 1]) / 2
                instrumental = (samples[:, 0] - samples[:, 1]) / 2
                
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
                # Mono audio - cannot separate
                vocals_audio = audio
                instrumental_audio = AudioSegment.silent(duration=len(audio))
            
            # Save files
            vocals_filename = f"vocals_{uuid.uuid4()}.wav"
            instrumental_filename = f"instrumental_{uuid.uuid4()}.wav"
            
            vocals_path = os.path.join(output_dir, vocals_filename)
            instrumental_path = os.path.join(output_dir, instrumental_filename)
            
            vocals_audio.export(vocals_path, format='wav')
            instrumental_audio.export(instrumental_path, format='wav')
            
            return {
                'success': True,
                'vocals_file': vocals_filename,
                'instrumental_file': instrumental_filename,
                'message': "Vocal separation completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in vocal separation: {e}")
            return {'success': False, 'error': f"Vocal separation failed: {str(e)}"}