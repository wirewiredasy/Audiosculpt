"""
Noise Reduction Microservice
Handles background noise removal and audio enhancement
"""
import os
import uuid
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, Any
import logging

try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
except ImportError:
    HAS_NOISEREDUCE = False
    nr = None

logger = logging.getLogger(__name__)

class NoiseReductionService:
    """Microservice for noise reduction"""
    
    async def reduce_noise(self, input_path: str, output_dir: str, 
                          noise_reduce_factor: float = 0.5) -> Dict[str, Any]:
        """Reduce background noise"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            
            if HAS_NOISEREDUCE and nr is not None:
                # Use noisereduce library if available
                reduced_noise = nr.reduce_noise(y=y, sr=sr, prop_decrease=noise_reduce_factor)
            else:
                # Fallback: Simple spectral gating using librosa
                stft = librosa.stft(y)
                magnitude = np.abs(stft)
                
                # Apply simple noise gate based on magnitude threshold
                threshold = np.percentile(magnitude, 20 * (1 - noise_reduce_factor))
                mask = magnitude > threshold
                
                # Apply the mask
                stft_filtered = stft * mask
                reduced_noise = librosa.istft(stft_filtered)
            
            output_filename = f"noise_reduced_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            sf.write(output_path, reduced_noise, sr)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Noise reduced by {noise_reduce_factor * 100}%"
            }
            
        except Exception as e:
            logger.error(f"Error reducing noise: {e}")
            return {'success': False, 'error': f"Noise reduction failed: {str(e)}"}