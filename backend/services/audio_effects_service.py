"""
Audio Effects Microservice
Handles reversal, equalizer, and other audio effects
"""
import os
import uuid
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from scipy import signal
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AudioEffectsService:
    """Microservice for audio effects"""
    
    async def reverse_audio(self, input_path: str, output_dir: str) -> Dict[str, Any]:
        """Reverse audio playback"""
        try:
            audio = AudioSegment.from_file(input_path)
            reversed_audio = audio.reverse()
            
            output_filename = f"reversed_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            reversed_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Audio reversed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error reversing audio: {e}")
            return {'success': False, 'error': f"Audio reversal failed: {str(e)}"}

    async def apply_equalizer(self, input_path: str, output_dir: str,
                             low_gain: float = 0, mid_gain: float = 0, high_gain: float = 0) -> Dict[str, Any]:
        """Apply 3-band equalizer"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            
            low_freq = 300
            high_freq = 3000
            nyquist = sr / 2
            
            if low_gain != 0:
                low_sos = signal.butter(4, low_freq / nyquist, btype='low', output='sos')
                low_filtered = signal.sosfilt(low_sos, y)
                low_filtered = low_filtered * (10 ** (low_gain / 20))
                y = y + (low_filtered - signal.sosfilt(low_sos, y))
            
            if high_gain != 0:
                high_sos = signal.butter(4, high_freq / nyquist, btype='high', output='sos')
                high_filtered = signal.sosfilt(high_sos, y)
                high_filtered = high_filtered * (10 ** (high_gain / 20))
                y = y + (high_filtered - signal.sosfilt(high_sos, y))
            
            if mid_gain != 0:
                mid_sos = signal.butter(4, [low_freq / nyquist, high_freq / nyquist], btype='band', output='sos')
                mid_filtered = signal.sosfilt(mid_sos, y)
                mid_filtered = mid_filtered * (10 ** (mid_gain / 20))
                y = y + (mid_filtered - signal.sosfilt(mid_sos, y))
            
            # Normalize to prevent clipping
            y = y / np.max(np.abs(y))
            
            output_filename = f"equalized_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            sf.write(output_path, y, sr)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Equalizer applied successfully"
            }
            
        except Exception as e:
            logger.error(f"Error applying equalizer: {e}")
            return {'success': False, 'error': f"Equalizer application failed: {str(e)}"}

    async def add_fade(self, input_path: str, output_dir: str,
                      fade_in_duration: float = 0, fade_out_duration: float = 0) -> Dict[str, Any]:
        """Add fade in/out effects"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            if fade_in_duration > 0:
                audio = audio.fade_in(int(fade_in_duration * 1000))
            
            if fade_out_duration > 0:
                audio = audio.fade_out(int(fade_out_duration * 1000))
            
            output_filename = f"faded_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Fade effects added (in: {fade_in_duration}s, out: {fade_out_duration}s)"
            }
            
        except Exception as e:
            logger.error(f"Error adding fade effects: {e}")
            return {'success': False, 'error': f"Fade effects failed: {str(e)}"}