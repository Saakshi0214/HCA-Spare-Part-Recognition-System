// ============================================================================
// CONFIGURATION
// ============================================================================
// If you are hosting the frontend on GitHub Pages and the backend on Render,
// set this variable to your Render app URL (e.g., 'https://hca-backend.onrender.com').
// If both frontend and backend are hosted on the same server, leave it empty ('').
const BACKEND_URL = 'https://hca-spare-part-recognition-system.onrender.com';

document.addEventListener('DOMContentLoaded', () => {

    // DOM Elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const cameraBtn = document.getElementById('cameraBtn');
    const clearBtn = document.getElementById('clearBtn');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const laserScanner = document.getElementById('laserScanner');

    // Status Badge
    const statusText = document.getElementById('statusText');
    const statusBadge = document.getElementById('statusBadge');

    // States
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const resultsContent = document.getElementById('resultsContent');

    // Result details
    const resultPartName = document.getElementById('resultPartName');
    const resultSubtext = document.getElementById('resultSubtext');
    const resultBanner = document.getElementById('resultBanner');
    const resultBannerIcon = document.getElementById('resultBannerIcon');
    const confidenceText = document.getElementById('confidenceText');
    const confidenceBar = document.getElementById('confidenceBar');

    // Metadata table elements
    const detailPartCode = document.getElementById('detailPartCode');
    const detailCategory = document.getElementById('detailCategory');
    const detailMachine = document.getElementById('detailMachine');
    const detailLocation = document.getElementById('detailLocation');
    const detailBin = document.getElementById('detailBin');
    const detailSold = document.getElementById('detailSold');
    const detailMatches = document.getElementById('detailMatches');
    const detailTime = document.getElementById('detailTime');
    const detailRemarks = document.getElementById('detailRemarks');

    // Advice Panel
    const advicePanel = document.getElementById('advicePanel');

    // Webcam elements
    const cameraModal = document.getElementById('cameraModal');
    const webcamVideo = document.getElementById('webcamVideo');
    const captureFrameBtn = document.getElementById('captureFrameBtn');
    const closeCameraBtn = document.getElementById('closeCameraBtn');

    let webcamStream = null;

    // Trigger browse file
    browseBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Drag and Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    dropZone.addEventListener('click', () => fileInput.click());

    // Reset UI
    clearBtn.addEventListener('click', resetUI);

    // Handle Uploaded File
    function handleFile(file) {
        if (!file.type.match('image.*')) {
            alert('Please upload an image file (PNG, JPG, JPEG).');
            return;
        }

        // Show image preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            dropZone.style.display = 'none';
            previewContainer.style.display = 'flex';
            uploadImage(file);
        };
        reader.readAsDataURL(file);
    }

    // Call predict API
    function uploadImage(fileBlob) {
        setUIState('processing');

        const formData = new FormData();
        formData.append('image', fileBlob, 'upload.jpg');

        fetch(`${BACKEND_URL}/predict`, {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || 'Server error occurred'); });
                }
                return response.json();
            })
            .then(data => {
                renderResults(data);
            })
            .catch(err => {
                console.error('Recognition error:', err);
                renderError(err.message);
            });
    }

    // Handle UI state changes
    function setUIState(state) {
        if (state === 'ready') {
            statusText.innerText = 'Server Ready';
            statusBadge.className = 'status-badge';
            laserScanner.style.display = 'none';
            emptyState.style.display = 'flex';
            loadingState.style.display = 'none';
            resultsContent.style.display = 'none';
            clearBtn.style.display = 'none';
        } else if (state === 'processing') {
            statusText.innerText = 'Analyzing Image';
            statusBadge.className = 'status-badge processing';
            laserScanner.style.display = 'block';
            emptyState.style.display = 'none';
            loadingState.style.display = 'flex';
            resultsContent.style.display = 'none';
            clearBtn.style.display = 'none';

            // Disable buttons during processing to prevent spamming
            browseBtn.disabled = true;
            cameraBtn.disabled = true;
        } else if (state === 'done') {
            laserScanner.style.display = 'none';
            loadingState.style.display = 'none';
            resultsContent.style.display = 'flex';
            clearBtn.style.display = 'inline-flex';

            browseBtn.disabled = false;
            cameraBtn.disabled = false;
        }
    }

    // Render recognition details
    function renderResults(data) {
        setUIState('done');

        if (data.part === 'Unknown' || data.confidence < 40) {
            statusText.innerText = 'Not in Database';
            statusBadge.className = 'status-badge error';

            resultBanner.className = 'result-banner not-found';
            resultBannerIcon.innerText = '❌';
            resultPartName.innerText = 'Part Not in Database';
            resultSubtext.innerText = 'This image does not contain a recognized spare part or it is not in the database.';

            confidenceText.innerText = '0%';
            confidenceBar.style.width = '0%';

            // Populate fallback info
            detailPartCode.innerHTML = '<span class="text-muted">N/A</span>';
            detailCategory.innerHTML = '<span class="text-muted">N/A</span>';
            detailMachine.innerHTML = '<span class="text-muted">N/A</span>';
            detailLocation.innerHTML = '<span class="text-muted">N/A</span>';
            detailBin.innerHTML = '<span class="text-muted">N/A</span>';
            detailSold.innerHTML = '<span class="text-muted">N/A</span>';
            detailRemarks.innerHTML = '<span class="text-muted">N/A</span>';

            detailMatches.innerText = `${data.matches} inliers (min 12 required)`;
            detailTime.innerText = `${data.processingTimeMs} ms`;

            advicePanel.style.display = 'flex';
        } else {
            statusText.innerText = 'Part Identified';
            statusBadge.className = 'status-badge';

            resultBanner.className = 'result-banner';
            resultBannerIcon.innerText = '✓';
            resultPartName.innerText = data.part;
            resultSubtext.innerText = `Spare part recognized with ${data.confidence}% confidence.`;

            confidenceText.innerText = `${data.confidence}%`;
            confidenceBar.style.width = `${data.confidence}%`;

            const details = data.details || {};

            // Populate actual details
            detailPartCode.innerHTML = details['Part Code'] ? `<span class="badge-chip">${details['Part Code']}</span>` : '<span class="text-muted">N/A</span>';
            detailCategory.innerText = details['Category'] || 'Feed Component';
            detailMachine.innerText = details['Machine Used In'] || 'Sewing Machine';
            detailLocation.innerHTML = details['Rack Location'] ? `<span class="badge-chip accent">${details['Rack Location']}</span>` : '<span class="text-muted">N/A</span>';
            detailBin.innerHTML = details['Bin Number'] ? `<span class="badge-chip accent">${details['Bin Number']}</span>` : '<span class="text-muted">N/A</span>';
            detailSold.innerText = details['Commonly Sold'] || 'N/A';
            detailRemarks.innerText = details['Remarks'] || 'No additional remarks';

            detailMatches.innerText = `${data.matches} descriptors`;
            detailTime.innerText = `${data.processingTimeMs} ms`;

            advicePanel.style.display = 'none';
        }
    }

    // Render error state
    function renderError(message) {
        setUIState('done');
        statusText.innerText = 'System Error';
        statusBadge.className = 'status-badge error';

        resultBanner.className = 'result-banner not-found';
        resultBannerIcon.innerText = '⚠';
        resultPartName.innerText = 'Analysis Error';
        resultSubtext.innerText = message || 'An error occurred while matching descriptors.';

        confidenceText.innerText = '0%';
        confidenceBar.style.width = '0%';

        detailPartCode.innerText = 'Error';
        detailCategory.innerText = 'Error';
        detailMachine.innerText = 'Error';
        detailLocation.innerText = 'Error';
        detailBin.innerText = 'Error';
        detailSold.innerText = 'Error';
        detailMatches.innerText = '0';
        detailTime.innerText = 'N/A';
        detailRemarks.innerText = 'Error processing request.';

        advicePanel.style.display = 'none';
    }

    // Reset GUI elements
    function resetUI() {
        previewImage.src = '';
        dropZone.style.display = 'flex';
        previewContainer.style.display = 'none';
        fileInput.value = '';
        setUIState('ready');
    }

    // =====================================
    // CAMERA / WEBCAM MANAGEMENT
    // =====================================

    cameraBtn.addEventListener('click', openWebcamModal);
    closeCameraBtn.addEventListener('click', closeWebcamModal);

    // Close modal if user clicks outside of content box
    cameraModal.addEventListener('click', (e) => {
        if (e.target === cameraModal) {
            closeWebcamModal();
        }
    });

    function openWebcamModal() {
        // Check if webcam API is available (requires HTTPS or localhost in modern browsers)
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn('getUserMedia not supported in this browser or context. Falling back to native device camera.');
            triggerCameraFallback();
            return;
        }

        cameraModal.style.display = 'flex';

        // Request browser camera stream
        navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "environment" // Prefer rear camera on mobile
            }
        })
            .then(stream => {
                webcamStream = stream;
                webcamVideo.srcObject = stream;
            })
            .catch(err => {
                console.error('Camera Access Error:', err);
                // If webcam access fails (e.g. permission denied), offer fallback to native device camera
                const useFallback = confirm('Failed to access live webcam: ' + err.message + '\n\nWould you like to capture a photo using your device\'s native camera app instead?');
                closeWebcamModal();
                if (useFallback) {
                    triggerCameraFallback();
                }
            });
    }

    function triggerCameraFallback() {
        // Temporarily configure fileInput for camera capture
        fileInput.setAttribute('capture', 'environment');

        // Setup a one-time change handler to clean up the capture attribute
        const resetCapture = () => {
            fileInput.removeAttribute('capture');
            fileInput.removeEventListener('change', resetCapture);
        };
        fileInput.addEventListener('change', resetCapture);

        // Trigger file select dialog (opens native camera on mobile devices)
        fileInput.click();

        // Clean up after a delay in case the dialog is cancelled
        setTimeout(() => {
            fileInput.removeAttribute('capture');
        }, 30000);
    }

    function closeWebcamModal() {
        cameraModal.style.display = 'none';

        // Stop stream and release webcam resources
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            webcamStream = null;
        }
        webcamVideo.srcObject = null;
    }

    captureFrameBtn.addEventListener('click', () => {
        if (!webcamStream) return;

        // Draw current video frame to hidden canvas
        const canvas = document.createElement('canvas');
        canvas.width = webcamVideo.videoWidth || 640;
        canvas.height = webcamVideo.videoHeight || 480;
        const ctx = canvas.getContext('2d');

        // Draw frame
        ctx.drawImage(webcamVideo, 0, 0, canvas.width, canvas.height);

        // Extract canvas image data as blob
        canvas.toBlob((blob) => {
            if (blob) {
                // Show preview on UI
                const url = URL.createObjectURL(blob);
                previewImage.src = url;
                dropZone.style.display = 'none';
                previewContainer.style.display = 'flex';

                // Submit blob
                uploadImage(blob);
            }
            closeWebcamModal();
        }, 'image/jpeg', 0.95);
    });

    // =====================================
    // BACKGROUND SLIDESHOW TRANSITIONS
    // =====================================
    const slides = document.querySelectorAll('.bg-slide');
    let currentSlide = 0;

    function nextSlide() {
        if (slides.length <= 1) return;
        slides[currentSlide].style.opacity = 0;
        currentSlide = (currentSlide + 1) % slides.length;
        slides[currentSlide].style.opacity = 1;
    }

    if (slides.length > 0) {
        setInterval(nextSlide, 5000); // Change background every 5 seconds
    }
});
