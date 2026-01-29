/**
 * Voice Input Module for CTV Booking
 * DOES: Records voice, transcribes to text, auto-fills form fields
 * INPUTS: Microphone audio from browser
 * OUTPUTS: Name and phone number extracted from speech
 */

// Voice recording state
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recordingTimeout = null;

// Maximum recording duration (10 seconds)
const MAX_RECORDING_DURATION = 10000;

/**
 * Toggle voice recording on/off
 */
async function toggleVoiceRecording() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        await startVoiceRecording();
    }
}

/**
 * Start voice recording
 */
async function startVoiceRecording() {
    const recordBtn = document.getElementById('voiceRecordBtn');
    const voiceStatus = document.getElementById('voiceStatus');
    const voiceResult = document.getElementById('voiceResult');

    try {
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });

        // Determine supported MIME type
        const mimeType = getSupportedMimeType();

        // Initialize MediaRecorder
        mediaRecorder = new MediaRecorder(stream, { mimeType });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());

            // Process audio
            await processRecordedAudio();
        };

        // Start recording
        mediaRecorder.start();
        isRecording = true;

        // Update UI to recording state
        recordBtn.classList.add('recording');
        voiceStatus.style.display = 'flex';
        voiceResult.style.display = 'none';

        const btnText = recordBtn.querySelector('.voice-pill-text');
        if (btnText) {
            btnText.textContent = t('tap_to_stop') || 'Nhấn để dừng';
        }

        // Auto-stop after max duration
        recordingTimeout = setTimeout(() => {
            if (isRecording) {
                stopVoiceRecording();
            }
        }, MAX_RECORDING_DURATION);

    } catch (error) {
        console.error('Microphone access error:', error);
        showVoiceError(t('mic_permission_denied') || 'Không thể truy cập microphone. Vui lòng cấp quyền.');
    }
}

/**
 * Stop voice recording
 */
function stopVoiceRecording() {
    if (recordingTimeout) {
        clearTimeout(recordingTimeout);
        recordingTimeout = null;
    }

    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        const recordBtn = document.getElementById('voiceRecordBtn');
        recordBtn.classList.remove('recording');
        recordBtn.classList.add('processing');

        const voiceStatus = document.getElementById('voiceStatus');
        const statusText = voiceStatus.querySelector('.voice-status-text');
        if (statusText) {
            statusText.textContent = t('processing') || 'Đang xử lý...';
        }
    }
}

/**
 * Process recorded audio and send to transcription API
 */
async function processRecordedAudio() {
    const recordBtn = document.getElementById('voiceRecordBtn');
    const voiceStatus = document.getElementById('voiceStatus');
    const voiceResult = document.getElementById('voiceResult');

    try {
        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

        // Check if blob is valid
        if (audioBlob.size < 1000) {
            showVoiceError(t('recording_too_short') || 'Bản ghi quá ngắn. Vui lòng nói lâu hơn.');
            resetVoiceUI();
            return;
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        // Send to transcription API
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success' || result.status === 'partial') {
            // Display results
            displayVoiceResults(result);

            // Auto-fill form fields
            if (result.name) {
                const nameInput = document.getElementById('bookingCustomerName');
                if (nameInput) {
                    nameInput.value = result.name;
                    highlightField(nameInput);
                }
            }

            if (result.phone) {
                const phoneInput = document.getElementById('bookingCustomerPhone');
                if (phoneInput) {
                    phoneInput.value = result.phone;
                    highlightField(phoneInput);

                    // Hide previous phone check result
                    const phoneResult = document.getElementById('bookingPhoneResult');
                    if (phoneResult) phoneResult.style.display = 'none';
                }
            }

            if (result.service) {
                const serviceInput = document.getElementById('bookingServiceInterest');
                if (serviceInput) {
                    serviceInput.value = result.service;
                    highlightField(serviceInput);
                }
            }

        } else {
            showVoiceError(result.message || t('transcription_failed') || 'Không thể nhận dạng giọng nói');
        }

    } catch (error) {
        console.error('Transcription error:', error);
        showVoiceError(t('transcription_failed') || 'Có lỗi xảy ra khi xử lý giọng nói');
    }

    resetVoiceUI();
}

/**
 * Display voice transcription results
 */
function displayVoiceResults(result) {
    const voiceResult = document.getElementById('voiceResult');
    const nameEl = document.getElementById('voiceDetectedName');
    const phoneEl = document.getElementById('voiceDetectedPhone');
    const serviceEl = document.getElementById('voiceDetectedService');
    const serviceTag = document.getElementById('voiceServiceTag');

    nameEl.textContent = result.name || '-';
    phoneEl.textContent = result.phone || '-';

    // Show service tag only if service was detected
    if (result.service && serviceEl && serviceTag) {
        serviceEl.textContent = result.service;
        serviceTag.style.display = 'inline-flex';
    } else if (serviceTag) {
        serviceTag.style.display = 'none';
    }

    voiceResult.style.display = 'flex';

    // Add success animation
    voiceResult.classList.add('success-animation');
    setTimeout(() => voiceResult.classList.remove('success-animation'), 600);
}

/**
 * Show voice error message
 */
function showVoiceError(message) {
    const voiceResult = document.getElementById('voiceResult');
    const nameEl = document.getElementById('voiceDetectedName');
    const phoneEl = document.getElementById('voiceDetectedPhone');

    nameEl.textContent = '❌ ' + message;
    phoneEl.textContent = '-';
    nameEl.style.color = '#e53e3e';

    voiceResult.style.display = 'flex';

    setTimeout(() => {
        nameEl.style.color = '';
    }, 3000);
}

/**
 * Reset voice UI to initial state
 */
function resetVoiceUI() {
    const recordBtn = document.getElementById('voiceRecordBtn');
    const voiceStatus = document.getElementById('voiceStatus');

    recordBtn.classList.remove('recording', 'processing');
    voiceStatus.style.display = 'none';

    const btnText = recordBtn.querySelector('.voice-pill-text');
    if (btnText) {
        btnText.textContent = t('voice_input_short') || 'Nhập giọng nói';
    }

    const statusText = voiceStatus.querySelector('.voice-status-text');
    if (statusText) {
        statusText.textContent = t('listening') || 'Đang nghe...';
    }
}

/**
 * Highlight a form field after auto-fill
 */
function highlightField(element) {
    element.classList.add('voice-filled');
    setTimeout(() => element.classList.remove('voice-filled'), 2000);
}

/**
 * Get supported MIME type for audio recording
 */
function getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4'
    ];

    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) {
            return type;
        }
    }

    return 'audio/webm';
}
