// Main application JavaScript
class AudioProcessorApp {
    constructor() {
        this.currentFileId = null;
        this.audioPlayer = null;
        this.processingStatus = null;
        this.init();
    }
    
    init() {
        this.setupFileUpload();
        this.setupEventListeners();
        this.createProcessingStatusElement();
    }
    
    setupFileUpload() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        // Drag and drop handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
        
        // Click to upload
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }
    
    setupEventListeners() {
        // Process buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-operation]')) {
                e.preventDefault();
                const operation = e.target.getAttribute('data-operation');
                this.showProcessingModal(operation);
            }
        });
        
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.processing-form')) {
                e.preventDefault();
                this.processAudio(e.target);
            }
        });
    }
    
    createProcessingStatusElement() {
        this.processingStatus = document.createElement('div');
        this.processingStatus.className = 'processing-status';
        document.body.appendChild(this.processingStatus);
    }
    
    showStatus(message, type = 'info') {
        this.processingStatus.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span>${message}</span>
            </div>
        `;
        this.processingStatus.classList.add('show');
        
        if (type !== 'processing') {
            setTimeout(() => {
                this.processingStatus.classList.remove('show');
            }, 3000);
        }
    }
    
    hideStatus() {
        this.processingStatus.classList.remove('show');
    }
    
    async handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        this.showStatus('Uploading file...', 'processing');
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentFileId = result.file_id;
                this.displayFileInfo(result);
                this.showProcessingOptions();
                this.hideStatus();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        }
    }
    
    displayFileInfo(fileInfo) {
        const infoContainer = document.getElementById('fileInfo');
        const audioInfo = fileInfo.audio_info;
        
        infoContainer.innerHTML = `
            <div class="file-info">
                <h5><i class="fas fa-file-audio"></i> ${fileInfo.original_name}</h5>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Duration:</strong> ${this.formatDuration(audioInfo.duration)}</p>
                        <p><strong>Format:</strong> ${audioInfo.format}</p>
                        <p><strong>Channels:</strong> ${audioInfo.channels}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Sample Rate:</strong> ${audioInfo.frame_rate} Hz</p>
                        <p><strong>Bit Depth:</strong> ${audioInfo.sample_width * 8} bit</p>
                        ${audioInfo.title ? `<p><strong>Title:</strong> ${audioInfo.title}</p>` : ''}
                    </div>
                </div>
            </div>
        `;
        
        infoContainer.style.display = 'block';
    }
    
    showProcessingOptions() {
        document.getElementById('processingOptions').style.display = 'block';
    }
    
    showProcessingModal(operation) {
        if (!this.currentFileId) {
            this.showError('Please upload a file first');
            return;
        }
        
        const modal = this.createProcessingModal(operation);
        document.body.appendChild(modal);
        
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    createProcessingModal(operation) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${this.getOperationTitle(operation)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${this.getOperationForm(operation)}
                    </div>
                </div>
            </div>
        `;
        
        return modal;
    }
    
    getOperationTitle(operation) {
        const titles = {
            'vocal_removal': 'Vocal Removal',
            'pitch_tempo': 'Pitch & Tempo Adjustment',
            'convert': 'Format Conversion',
            'cut': 'Audio Cutting',
            'noise_reduction': 'Noise Reduction',
            'normalize': 'Volume Normalization',
            'fade': 'Fade Effects',
            'reverse': 'Reverse Audio',
            'equalizer': 'Equalizer',
            'metadata': 'Edit Metadata'
        };
        return titles[operation] || 'Audio Processing';
    }
    
    getOperationForm(operation) {
        switch (operation) {
            case 'vocal_removal':
                return `
                    <form class="processing-form" data-operation="vocal_removal">
                        <p>This will separate vocals from instrumental tracks using advanced audio processing.</p>
                        <button type="submit" class="btn btn-audio">Remove Vocals</button>
                    </form>
                `;
                
            case 'pitch_tempo':
                return `
                    <form class="processing-form" data-operation="pitch_tempo">
                        <div class="mb-3">
                            <label class="form-label">Pitch Shift (semitones)</label>
                            <input type="range" class="form-range" name="pitch_shift" min="-12" max="12" value="0" step="1">
                            <div class="d-flex justify-content-between">
                                <span>-12</span><span id="pitchValue">0</span><span>+12</span>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Tempo Change</label>
                            <input type="range" class="form-range" name="tempo_change" min="0.5" max="2.0" value="1.0" step="0.1">
                            <div class="d-flex justify-content-between">
                                <span>0.5x</span><span id="tempoValue">1.0x</span><span>2.0x</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-audio">Apply Changes</button>
                    </form>
                `;
                
            case 'convert':
                return `
                    <form class="processing-form" data-operation="convert">
                        <div class="mb-3">
                            <label class="form-label">Output Format</label>
                            <select class="form-select" name="format" required>
                                <option value="mp3">MP3</option>
                                <option value="wav">WAV</option>
                                <option value="ogg">OGG</option>
                                <option value="m4a">M4A</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-audio">Convert</button>
                    </form>
                `;
                
            case 'cut':
                return `
                    <form class="processing-form" data-operation="cut">
                        <div class="mb-3">
                            <label class="form-label">Start Time (seconds)</label>
                            <input type="number" class="form-control" name="start_time" min="0" step="0.1" value="0" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">End Time (seconds)</label>
                            <input type="number" class="form-control" name="end_time" min="0" step="0.1" value="30" required>
                        </div>
                        <button type="submit" class="btn btn-audio">Cut Audio</button>
                    </form>
                `;
                
            case 'noise_reduction':
                return `
                    <form class="processing-form" data-operation="noise_reduction">
                        <div class="mb-3">
                            <label class="form-label">Noise Reduction Level</label>
                            <input type="range" class="form-range" name="noise_factor" min="0.1" max="1.0" value="0.5" step="0.1">
                            <div class="d-flex justify-content-between">
                                <span>Light</span><span id="noiseValue">Medium</span><span>Heavy</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-audio">Reduce Noise</button>
                    </form>
                `;
                
            case 'normalize':
                return `
                    <form class="processing-form" data-operation="normalize">
                        <div class="mb-3">
                            <label class="form-label">Target Volume (dBFS)</label>
                            <input type="range" class="form-range" name="target_db" min="-30" max="0" value="-20" step="1">
                            <div class="d-flex justify-content-between">
                                <span>-30dB</span><span id="dbValue">-20dB</span><span>0dB</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-audio">Normalize</button>
                    </form>
                `;
                
            case 'fade':
                return `
                    <form class="processing-form" data-operation="fade">
                        <div class="mb-3">
                            <label class="form-label">Fade In Duration (seconds)</label>
                            <input type="number" class="form-control" name="fade_in" min="0" step="0.1" value="0">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Fade Out Duration (seconds)</label>
                            <input type="number" class="form-control" name="fade_out" min="0" step="0.1" value="0">
                        </div>
                        <button type="submit" class="btn btn-audio">Apply Fade</button>
                    </form>
                `;
                
            case 'reverse':
                return `
                    <form class="processing-form" data-operation="reverse">
                        <p>This will reverse the audio playback completely.</p>
                        <button type="submit" class="btn btn-audio">Reverse Audio</button>
                    </form>
                `;
                
            case 'equalizer':
                return `
                    <form class="processing-form" data-operation="equalizer">
                        <div class="equalizer-controls">
                            <div class="eq-band">
                                <label>Low</label>
                                <input type="range" class="eq-slider" name="low_gain" min="-20" max="20" value="0" step="1">
                                <span id="lowValue">0dB</span>
                            </div>
                            <div class="eq-band">
                                <label>Mid</label>
                                <input type="range" class="eq-slider" name="mid_gain" min="-20" max="20" value="0" step="1">
                                <span id="midValue">0dB</span>
                            </div>
                            <div class="eq-band">
                                <label>High</label>
                                <input type="range" class="eq-slider" name="high_gain" min="-20" max="20" value="0" step="1">
                                <span id="highValue">0dB</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-audio">Apply EQ</button>
                    </form>
                `;
                
            case 'metadata':
                return `
                    <form class="processing-form" data-operation="metadata">
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="title">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Artist</label>
                            <input type="text" class="form-control" name="artist">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Album</label>
                            <input type="text" class="form-control" name="album">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Album Artist</label>
                            <input type="text" class="form-control" name="albumartist">
                        </div>
                        <button type="submit" class="btn btn-audio">Save Metadata</button>
                    </form>
                `;
                
            default:
                return '<p>Operation not implemented yet.</p>';
        }
    }
    
    async processAudio(form) {
        const operation = form.getAttribute('data-operation');
        const formData = new FormData(form);
        
        // Build parameters object
        const params = {};
        for (let [key, value] of formData.entries()) {
            params[key] = value;
        }
        
        // Special handling for metadata
        if (operation === 'metadata') {
            params.metadata = {};
            for (let [key, value] of formData.entries()) {
                if (value.trim()) {
                    params.metadata[key] = value;
                }
            }
        }
        
        this.showStatus('Processing audio...', 'processing');
        
        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    operation: operation,
                    file_id: this.currentFileId,
                    params: params
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.hideStatus();
                bootstrap.Modal.getInstance(form.closest('.modal')).hide();
                
                if (operation === 'vocal_removal') {
                    this.showSeparationResults(result);
                } else {
                    this.showProcessingResult(result.processed_file);
                }
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.showError('Processing failed: ' + error.message);
        }
    }
    
    showSeparationResults(result) {
        const resultsContainer = document.getElementById('resultsContainer');
        resultsContainer.innerHTML = `
            <div class="audio-card p-4 mb-4">
                <h5><i class="fas fa-music"></i> Vocal Separation Complete</h5>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Vocals Track</h6>
                        <audio controls class="w-100 mb-2">
                            <source src="/download/${result.vocals_file}" type="audio/wav">
                        </audio>
                        <a href="/download/${result.vocals_file}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-download"></i> Download Vocals
                        </a>
                    </div>
                    <div class="col-md-6">
                        <h6>Instrumental Track</h6>
                        <audio controls class="w-100 mb-2">
                            <source src="/download/${result.instrumental_file}" type="audio/wav">
                        </audio>
                        <a href="/download/${result.instrumental_file}" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-download"></i> Download Instrumental
                        </a>
                    </div>
                </div>
            </div>
        `;
        resultsContainer.style.display = 'block';
    }
    
    showProcessingResult(filename) {
        const resultsContainer = document.getElementById('resultsContainer');
        resultsContainer.innerHTML = `
            <div class="audio-card p-4 mb-4">
                <h5><i class="fas fa-check-circle text-success"></i> Processing Complete</h5>
                <audio controls class="w-100 mb-3">
                    <source src="/download/${filename}" type="audio/wav">
                </audio>
                <a href="/download/${filename}" class="btn btn-audio">
                    <i class="fas fa-download"></i> Download Processed Audio
                </a>
            </div>
        `;
        resultsContainer.style.display = 'block';
        
        // Initialize audio player for the result
        const audioElement = resultsContainer.querySelector('audio');
        if (this.audioPlayer) {
            this.audioPlayer.destroy();
        }
        this.audioPlayer = new AudioPlayer(audioElement, {
            showVolumeControls: true,
            separateVocalControls: filename.includes('vocals') || filename.includes('instrumental')
        });
    }
    
    showError(message) {
        this.hideStatus();
        
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.container').insertBefore(alert, document.querySelector('.container').firstChild);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
    
    formatDuration(seconds) {
        if (isNaN(seconds)) return '0:00';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AudioProcessorApp();
    
    // Update slider values in real-time
    document.addEventListener('input', (e) => {
        if (e.target.name === 'pitch_shift') {
            document.getElementById('pitchValue').textContent = e.target.value;
        } else if (e.target.name === 'tempo_change') {
            document.getElementById('tempoValue').textContent = e.target.value + 'x';
        } else if (e.target.name === 'noise_factor') {
            const levels = ['Light', 'Light', 'Light', 'Medium', 'Medium', 'Medium', 'Heavy', 'Heavy', 'Heavy', 'Heavy'];
            const index = Math.floor(parseFloat(e.target.value) * 10) - 1;
            document.getElementById('noiseValue').textContent = levels[index] || 'Medium';
        } else if (e.target.name === 'target_db') {
            document.getElementById('dbValue').textContent = e.target.value + 'dB';
        } else if (e.target.name === 'low_gain') {
            document.getElementById('lowValue').textContent = e.target.value + 'dB';
        } else if (e.target.name === 'mid_gain') {
            document.getElementById('midValue').textContent = e.target.value + 'dB';
        } else if (e.target.name === 'high_gain') {
            document.getElementById('highValue').textContent = e.target.value + 'dB';
        }
    });
});
