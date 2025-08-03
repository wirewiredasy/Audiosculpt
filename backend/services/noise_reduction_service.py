
"""
Enhanced Noise Reduction Microservice
Advanced background noise removal and audio enhancement
"""
import os
import uuid
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, Any
import logging
from scipy import signal

try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
except ImportError:
    HAS_NOISEREDUCE = False
    nr = None

logger = logging.getLogger(__name__)

class NoiseReductionService:
    """Enhanced Microservice for noise reduction"""
    
    async def reduce_noise(self, input_path: str, output_dir: str, 
                          noise_reduce_factor: float = 0.5) -> Dict[str, Any]:
        """Advanced noise reduction with multiple techniques"""
        try:
            print(f"🔧 Loading audio file: {input_path}")
            y, sr = librosa.load(input_path, sr=None)
            print(f"📊 Audio loaded - Sample rate: {sr}Hz, Duration: {len(y)/sr:.2f}s")
            
            # Method 1: Use noisereduce if available (best quality)
            if HAS_NOISEREDUCE and nr is not None:
                print("🚀 Using advanced noisereduce library...")
                reduced_noise = nr.reduce_noise(
                    y=y, 
                    sr=sr, 
                    prop_decrease=noise_reduce_factor,
                    stationary=False,  # Better for non-stationary noise
                    n_fft=2048,
                    win_length=2048
                )
                method_used = "Advanced Noisereduce"
            else:
                print("⚡ Using enhanced spectral gating...")
                reduced_noise = self._enhanced_spectral_gating(y, sr, noise_reduce_factor)
                method_used = "Enhanced Spectral Gating"
            
            # Additional post-processing
            print("🎛️ Applying post-processing...")
            reduced_noise = self._post_process_audio(reduced_noise, sr)
            
            output_filename = f"noise_reduced_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            sf.write(output_path, reduced_noise, sr)
            
            print(f"✅ Noise reduction complete using {method_used}")
            print(f"💾 Saved to: {output_filename}")
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Advanced noise reduced by {noise_reduce_factor * 100}% using {method_used}"
            }
            
        except Exception as e:
            logger.error(f"Error reducing noise: {e}")
            print(f"❌ Error: {str(e)}")
            return {'success': False, 'error': f"Noise reduction failed: {str(e)}"}
    
    def _enhanced_spectral_gating(self, y: np.ndarray, sr: int, noise_factor: float) -> np.ndarray:
        """Enhanced spectral gating with multiple frequency analysis"""
        print("🔍 Analyzing audio spectrum...")
        
        # Use larger window for better frequency resolution
        n_fft = 4096
        hop_length = n_fft // 4
        
        # Compute STFT
        stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Multi-band noise estimation
        print("📈 Estimating noise profile across frequency bands...")
        
        # Low frequencies (0-1kHz) - usually less noise
        low_freq_bins = int(1000 * n_fft / sr)
        low_thresh = np.percentile(magnitude[:low_freq_bins], 15 * (1 - noise_factor))
        
        # Mid frequencies (1-8kHz) - most important for speech
        mid_freq_bins = int(8000 * n_fft / sr)
        mid_thresh = np.percentile(magnitude[low_freq_bins:mid_freq_bins], 25 * (1 - noise_factor))
        
        # High frequencies (8kHz+) - often contains noise
        high_thresh = np.percentile(magnitude[mid_freq_bins:], 35 * (1 - noise_factor))
        
        # Create frequency-dependent threshold
        threshold = np.zeros_like(magnitude)
        threshold[:low_freq_bins] = low_thresh
        threshold[low_freq_bins:mid_freq_bins] = mid_thresh
        threshold[mid_freq_bins:] = high_thresh
        
        # Smooth gating mask to avoid artifacts
        print("🎯 Creating smooth gating mask...")
        raw_mask = magnitude > threshold
        
        # Apply median filter to smooth the mask
        from scipy.ndimage import median_filter
        smooth_mask = median_filter(raw_mask.astype(float), size=(3, 3))
        
        # Gradual gating instead of hard cutoff
        gate_strength = 0.1 + 0.9 * smooth_mask  # 10% to 100% strength
        
        # Apply the mask
        stft_filtered = stft * gate_strength
        
        # Reconstruct audio
        print("🔧 Reconstructing audio...")
        result = librosa.istft(stft_filtered, hop_length=hop_length)
        
        return result
    
    def _post_process_audio(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Post-processing to enhance audio quality"""
        print("✨ Applying audio enhancements...")
        
        # 1. Gentle high-pass filter to remove low-frequency rumble
        nyquist = sr / 2
        low_cutoff = 80 / nyquist  # 80 Hz cutoff
        b, a = signal.butter(4, low_cutoff, btype='high')
        audio = signal.filtfilt(b, a, audio)
        
        # 2. Subtle compression to even out volume
        audio = self._gentle_compress(audio)
        
        # 3. Normalize to prevent clipping
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio * (0.95 / max_val)
        
        return audio
    
    def _gentle_compress(self, audio: np.ndarray, threshold: float = 0.7, ratio: float = 4.0) -> np.ndarray:
        """Apply gentle compression to audio"""
        # Simple soft-knee compressor
        abs_audio = np.abs(audio)
        compressed = np.copy(audio)
        
        # Find samples above threshold
        over_threshold = abs_audio > threshold
        
        if np.any(over_threshold):
            # Apply compression formula
            excess = abs_audio[over_threshold] - threshold
            compressed_excess = excess / ratio
            new_magnitude = threshold + compressed_excess
            
            # Maintain original sign
            sign = np.sign(audio[over_threshold])
            compressed[over_threshold] = sign * new_magnitude
        
        return compressed
    
    async def reduce_noise_aggressive(self, input_path: str, output_dir: str, 
                                    noise_reduce_factor: float = 0.8) -> Dict[str, Any]:
        """Aggressive noise reduction for very noisy audio"""
        try:
            print("🔥 Starting aggressive noise reduction...")
            
            # Load with higher precision
            y, sr = librosa.load(input_path, sr=None)
            
            # Multi-pass noise reduction
            print("🔄 Applying multi-pass noise reduction...")
            result = y
            
            # Pass 1: Spectral subtraction
            result = self._spectral_subtraction(result, sr, noise_reduce_factor)
            
            # Pass 2: Enhanced spectral gating
            result = self._enhanced_spectral_gating(result, sr, noise_reduce_factor * 0.7)
            
            # Pass 3: Wiener filtering
            result = self._wiener_filter(result, sr)
            
            # Final post-processing
            result = self._post_process_audio(result, sr)
            
            output_filename = f"aggressive_denoised_{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, output_filename)
            sf.write(output_path, result, sr)
            
            print("✅ Aggressive noise reduction complete!")
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Aggressive noise reduction applied ({noise_reduce_factor * 100}%)"
            }
            
        except Exception as e:
            logger.error(f"Error in aggressive noise reduction: {e}")
            return {'success': False, 'error': str(e)}
    
    def _spectral_subtraction(self, audio: np.ndarray, sr: int, factor: float) -> np.ndarray:
        """Spectral subtraction noise reduction"""
        stft = librosa.stft(audio, n_fft=2048)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise from first 0.5 seconds
        noise_frames = int(0.5 * sr / (2048 // 4))
        noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Subtract noise spectrum
        clean_magnitude = magnitude - factor * noise_spectrum
        clean_magnitude = np.maximum(clean_magnitude, 0.1 * magnitude)  # Floor
        
        # Reconstruct
        clean_stft = clean_magnitude * np.exp(1j * phase)
        return librosa.istft(clean_stft)
    
    def _wiener_filter(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Simple Wiener filtering for noise reduction"""
        # Estimate signal power vs noise power
        stft = librosa.stft(audio, n_fft=1024)
        power = np.abs(stft) ** 2
        
        # Estimate noise power from quieter frames
        frame_power = np.mean(power, axis=0)
        noise_power = np.percentile(frame_power, 20)
        
        # Wiener gain
        wiener_gain = power / (power + noise_power)
        wiener_gain = np.maximum(wiener_gain, 0.1)  # Minimum gain
        
        # Apply filter
        filtered_stft = stft * wiener_gain
        return librosa.istft(filtered_stft)
