class AudioPlayer {
    constructor(audioElement, options = {}) {
        this.audio = audioElement;
        this.options = {
            showWaveform: options.showWaveform || false,
            showVolumeControls: options.showVolumeControls || true,
            separateVocalControls: options.separateVocalControls || false,
            ...options
        };
        
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        this.volume = 1;
        this.vocalVolume = 1;
        this.instrumentalVolume = 1;
        
        this.init();
    }
    
    init() {
        this.createControls();
        this.bindEvents();
        
        if (this.options.showWaveform) {
            this.initWaveform();
        }
    }
    
    createControls() {
        const container = document.createElement('div');
        container.className = 'audio-player';
        container.innerHTML = `
            <div class="audio-info mb-3">
                <h5 class="mb-1">Audio Player</h5>
                <small class="text-muted">Ready to play</small>
            </div>
            
            <div class="audio-controls">
                <button class="play-button" id="playBtn">
                    <i class="fas fa-play"></i>
                </button>
                
                <div class="time-display">
                    <span id="currentTime">0:00</span> / <span id="totalTime">0:00</span>
                </div>
                
                <div class="progress-container" id="progressContainer">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                
                ${this.options.showVolumeControls ? this.createVolumeControls() : ''}
            </div>
            
            ${this.options.separateVocalControls ? this.createSeparateControls() : ''}
            
            ${this.options.showWaveform ? '<div class="waveform-container"><canvas class="waveform" id="waveform"></canvas></div>' : ''}
        `;
        
        // Insert after the audio element
        this.audio.parentNode.insertBefore(container, this.audio.nextSibling);
        this.container = container;
        
        // Get control elements
        this.playBtn = container.querySelector('#playBtn');
        this.currentTimeEl = container.querySelector('#currentTime');
        this.totalTimeEl = container.querySelector('#totalTime');
        this.progressContainer = container.querySelector('#progressContainer');
        this.progressBar = container.querySelector('#progressBar');
        this.volumeSlider = container.querySelector('#volumeSlider');
        this.vocalVolumeSlider = container.querySelector('#vocalVolume');
        this.instrumentalVolumeSlider = container.querySelector('#instrumentalVolume');
    }
    
    createVolumeControls() {
        return `
            <div class="volume-control">
                <i class="fas fa-volume-up"></i>
                <input type="range" class="volume-slider" id="volumeSlider" 
                       min="0" max="100" value="100">
            </div>
        `;
    }
    
    createSeparateControls() {
        return `
            <div class="separate-controls mt-3">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">
                            <i class="fas fa-microphone"></i> Vocals Volume
                        </label>
                        <input type="range" class="form-range" id="vocalVolume" 
                               min="0" max="100" value="100">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">
                            <i class="fas fa-music"></i> Instrumental Volume
                        </label>
                        <input type="range" class="form-range" id="instrumentalVolume" 
                               min="0" max="100" value="100">
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Play/pause button
        this.playBtn.addEventListener('click', () => this.togglePlay());
        
        // Audio events
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.onEnded());
        
        // Progress bar
        this.progressContainer.addEventListener('click', (e) => this.seek(e));
        
        // Volume controls
        if (this.volumeSlider) {
            this.volumeSlider.addEventListener('input', (e) => this.setVolume(e.target.value / 100));
        }
        
        if (this.vocalVolumeSlider) {
            this.vocalVolumeSlider.addEventListener('input', (e) => this.setVocalVolume(e.target.value / 100));
        }
        
        if (this.instrumentalVolumeSlider) {
            this.instrumentalVolumeSlider.addEventListener('input', (e) => this.setInstrumentalVolume(e.target.value / 100));
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    initWaveform() {
        const canvas = this.container.querySelector('#waveform');
        if (!canvas) return;
        
        this.waveformCanvas = canvas;
        this.waveformCtx = canvas.getContext('2d');
        
        // Set canvas size
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        
        this.drawWaveform();
    }
    
    drawWaveform() {
        if (!this.waveformCtx || !this.audio.src) return;
        
        // Simple waveform visualization
        const ctx = this.waveformCtx;
        const canvas = this.waveformCanvas;
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        
        // Draw placeholder waveform
        ctx.strokeStyle = 'rgba(108, 92, 231, 0.6)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < width; i += 4) {
            const amplitude = Math.random() * height * 0.6 + height * 0.2;
            ctx.moveTo(i, height / 2);
            ctx.lineTo(i, height / 2 - amplitude / 2);
            ctx.moveTo(i, height / 2);
            ctx.lineTo(i, height / 2 + amplitude / 2);
        }
        
        ctx.stroke();
        
        // Draw progress line
        if (this.duration > 0) {
            const progress = (this.currentTime / this.duration) * width;
            ctx.strokeStyle = '#fd79a8';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(progress, 0);
            ctx.lineTo(progress, height);
            ctx.stroke();
        }
    }
    
    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    play() {
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.playBtn.innerHTML = '<i class="fas fa-pause"></i>';
        }).catch(error => {
            console.error('Error playing audio:', error);
        });
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
    
    seek(event) {
        const rect = this.progressContainer.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const percentage = clickX / rect.width;
        const newTime = percentage * this.duration;
        
        this.audio.currentTime = newTime;
    }
    
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        this.audio.volume = this.volume;
    }
    
    setVocalVolume(volume) {
        this.vocalVolume = Math.max(0, Math.min(1, volume));
        // This would require separate audio tracks in a real implementation
        console.log('Vocal volume:', this.vocalVolume);
    }
    
    setInstrumentalVolume(volume) {
        this.instrumentalVolume = Math.max(0, Math.min(1, volume));
        // This would require separate audio tracks in a real implementation
        console.log('Instrumental volume:', this.instrumentalVolume);
    }
    
    updateDuration() {
        this.duration = this.audio.duration;
        this.totalTimeEl.textContent = this.formatTime(this.duration);
    }
    
    updateProgress() {
        this.currentTime = this.audio.currentTime;
        this.currentTimeEl.textContent = this.formatTime(this.currentTime);
        
        const percentage = (this.currentTime / this.duration) * 100;
        this.progressBar.style.width = `${percentage}%`;
        
        if (this.options.showWaveform) {
            this.drawWaveform();
        }
    }
    
    onEnded() {
        this.isPlaying = false;
        this.playBtn.innerHTML = '<i class="fas fa-play"></i>';
        this.progressBar.style.width = '0%';
    }
    
    handleKeyboard(event) {
        if (event.target.tagName === 'INPUT') return;
        
        switch (event.code) {
            case 'Space':
                event.preventDefault();
                this.togglePlay();
                break;
            case 'ArrowLeft':
                event.preventDefault();
                this.audio.currentTime = Math.max(0, this.audio.currentTime - 10);
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.audio.currentTime = Math.min(this.duration, this.audio.currentTime + 10);
                break;
        }
    }
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    loadAudio(src, title = 'Audio File') {
        this.audio.src = src;
        this.container.querySelector('.audio-info h5').textContent = title;
        this.container.querySelector('.audio-info small').textContent = 'Loading...';
        
        this.audio.addEventListener('loadeddata', () => {
            this.container.querySelector('.audio-info small').textContent = 'Ready to play';
        }, { once: true });
    }
    
    destroy() {
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

// Export for use in other scripts
window.AudioPlayer = AudioPlayer;
