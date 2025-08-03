"""
Pitch and Tempo Adjustment Microservice
Handles pitch shifting and tempo changes
"""
import os
import uuid
import librosa
import soundfile as sf
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PitchTempoService:
    """Microservice for pitch and tempo adjustment"""
    
    async def change_pitch_tempo(self, input_path: str, output_dir: str, 
                                pitch_shift: float = 0, tempo_change: float = 1.0) -> Dict[str, Any]:
        """Change pitch and tempo of audio"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            
            # Apply pitch shift (in semitones)
            if pitch_shift != 0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)
            
            # Apply tempo change
            if tempo_change != 1.0:
                y = librosa.effects.time_stretch(y, rate=tempo_change)
            
            output_filename = f"pitch_tempo_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            sf.write(output_path, y, sr)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Pitch shifted by {pitch_shift} semitones, tempo changed by {tempo_change}x"
            }
            
        except Exception as e:
            logger.error(f"Error changing pitch/tempo: {e}")
            return {'success': False, 'error': f"Pitch/tempo adjustment failed: {str(e)}"}