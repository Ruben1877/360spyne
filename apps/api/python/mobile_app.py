"""
MOBILE APP - Clone Spyne
========================
Application mobile avec guide de cadrage pour photographier des voitures.
- Camera en mode paysage
- Silhouette de guidage
- Capture 360° avec angles guides
- Segmentation automatique

Lance: python mobile_app.py
Puis: ngrok http 5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import io
import numpy as np
from PIL import Image
import cv2

try:
    from rembg import remove, new_session
except ImportError:
    os.system("pip install rembg[cpu] flask flask-cors")
    from rembg import remove, new_session

app = Flask(__name__)
CORS(app)

print("Chargement du modele ISNet...")
SESSION = new_session("isnet-general-use")
print("Modele charge!")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "captures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Angles pour la capture 360
ANGLES_360 = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180,
              190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350]


@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="screen-orientation" content="landscape">
    <title>Spyne Camera</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: #000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .app {
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: #000;
        }
        
        /* Camera View */
        .camera-container {
            flex: 1;
            position: relative;
            overflow: hidden;
        }
        
        #video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* Overlay avec guide de cadrage */
        .overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        
        /* Silhouette de voiture - Guide */
        .car-silhouette {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 70%;
            height: auto;
            opacity: 0.4;
        }
        
        /* Lignes de guidage */
        .guide-lines {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        
        .guide-lines svg {
            width: 100%;
            height: 100%;
        }
        
        /* Zone de cadrage centrale */
        .frame-zone {
            position: absolute;
            top: 10%;
            left: 10%;
            width: 80%;
            height: 75%;
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 8px;
        }
        
        .frame-zone::before {
            content: '';
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 10px solid transparent;
            border-right: 10px solid transparent;
            border-bottom: 10px solid rgba(255, 255, 255, 0.7);
        }
        
        /* Coins du cadre */
        .corner {
            position: absolute;
            width: 30px;
            height: 30px;
            border: 3px solid #00ff88;
        }
        .corner.tl { top: 10%; left: 10%; border-right: none; border-bottom: none; }
        .corner.tr { top: 10%; right: 10%; border-left: none; border-bottom: none; }
        .corner.bl { bottom: 15%; left: 10%; border-right: none; border-top: none; }
        .corner.br { bottom: 15%; right: 10%; border-left: none; border-top: none; }
        
        /* Ligne d'horizon */
        .horizon-line {
            position: absolute;
            top: 60%;
            left: 10%;
            width: 80%;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        }
        
        /* Indicateur d'angle */
        .angle-indicator {
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: #00ff88;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 18px;
            font-weight: 600;
        }
        
        /* Progress bar pour 360 */
        .progress-360 {
            position: absolute;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 4px;
        }
        
        .progress-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
        }
        
        .progress-dot.captured {
            background: #00ff88;
        }
        
        .progress-dot.current {
            background: #fff;
            transform: scale(1.3);
        }
        
        /* Instructions */
        .instructions {
            position: absolute;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.6);
            color: #fff;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            text-align: center;
            max-width: 80%;
        }
        
        /* Barre de controles */
        .controls {
            height: 90px;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 0 20px;
        }
        
        .btn {
            background: none;
            border: none;
            color: #fff;
            font-size: 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            padding: 10px;
        }
        
        .btn svg {
            width: 28px;
            height: 28px;
            fill: currentColor;
        }
        
        .btn-capture {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: #fff;
            border: 4px solid #00ff88;
            position: relative;
        }
        
        .btn-capture::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: #00ff88;
        }
        
        .btn-capture:active::after {
            background: #00cc6a;
        }
        
        /* Mode selector */
        .mode-selector {
            position: absolute;
            bottom: 100px;
            left: 20px;
            display: flex;
            gap: 10px;
        }
        
        .mode-btn {
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 20px;
            color: #fff;
            font-size: 12px;
            cursor: pointer;
        }
        
        .mode-btn.active {
            background: #00ff88;
            color: #000;
            border-color: #00ff88;
        }
        
        /* Counter */
        .capture-counter {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            color: #fff;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 16px;
        }
        
        /* Gallery preview */
        .gallery-preview {
            position: absolute;
            bottom: 100px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 8px;
            border: 2px solid #fff;
            overflow: hidden;
            cursor: pointer;
        }
        
        .gallery-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* Rotate prompt for portrait */
        .rotate-prompt {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #000;
            z-index: 9999;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: #fff;
        }
        
        .rotate-prompt svg {
            width: 80px;
            height: 80px;
            fill: #00ff88;
            animation: rotate 2s ease-in-out infinite;
        }
        
        @keyframes rotate {
            0%, 100% { transform: rotate(0deg); }
            50% { transform: rotate(90deg); }
        }
        
        .rotate-prompt p {
            margin-top: 20px;
            font-size: 18px;
        }
        
        @media (orientation: portrait) {
            .rotate-prompt {
                display: flex;
            }
            .app {
                display: none;
            }
        }
        
        /* Loading */
        .loading-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            color: #fff;
        }
        
        .loading-overlay.show {
            display: flex;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #333;
            border-top-color: #00ff88;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Flash effect */
        .flash {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #fff;
            opacity: 0;
            pointer-events: none;
            z-index: 999;
        }
        
        .flash.active {
            animation: flash 0.2s ease-out;
        }
        
        @keyframes flash {
            0% { opacity: 0.8; }
            100% { opacity: 0; }
        }
    </style>
</head>
<body>
    <!-- Rotate prompt pour portrait -->
    <div class="rotate-prompt">
        <svg viewBox="0 0 24 24"><path d="M16.48 2.52c3.27 1.55 5.61 4.72 5.97 8.48h1.5C23.44 4.84 18.29 0 12 0l-.66.03 3.81 3.81 1.33-1.32zm-6.25-.77c-.59-.59-1.54-.59-2.12 0L1.75 8.11c-.59.59-.59 1.54 0 2.12l12.02 12.02c.59.59 1.54.59 2.12 0l6.36-6.36c-.59.59-1.54.59-2.12 0L10.23 1.75zM4.22 8.58l5.79-5.79L20.58 13.36l-5.79 5.79L4.22 8.58zM7.52 21.48C4.25 19.94 1.91 16.76 1.55 13H.05C.56 19.16 5.71 24 12 24l.66-.03-3.81-3.81-1.33 1.32z"/></svg>
        <p>Tourne ton telephone en paysage</p>
    </div>
    
    <!-- App principale -->
    <div class="app">
        <div class="camera-container">
            <video id="video" autoplay playsinline></video>
            
            <div class="overlay">
                <!-- Coins de cadrage -->
                <div class="corner tl"></div>
                <div class="corner tr"></div>
                <div class="corner bl"></div>
                <div class="corner br"></div>
                
                <!-- Zone de cadrage -->
                <div class="frame-zone"></div>
                
                <!-- Ligne d'horizon -->
                <div class="horizon-line"></div>
                
                <!-- Silhouette de voiture SVG -->
                <svg class="car-silhouette" viewBox="0 0 400 150" fill="none" stroke="#00ff88" stroke-width="2">
                    <!-- Carrosserie -->
                    <path d="M50 100 L80 100 L100 60 L150 40 L250 40 L300 60 L320 100 L350 100" stroke-linecap="round"/>
                    <!-- Toit -->
                    <path d="M120 40 L130 20 L270 20 L280 40" stroke-linecap="round"/>
                    <!-- Roue avant -->
                    <circle cx="100" cy="110" r="25" />
                    <circle cx="100" cy="110" r="15" />
                    <!-- Roue arriere -->
                    <circle cx="300" cy="110" r="25" />
                    <circle cx="300" cy="110" r="15" />
                    <!-- Vitres -->
                    <path d="M135 22 L145 40 L180 40 L175 22 Z" fill="rgba(0,255,136,0.1)"/>
                    <path d="M185 22 L180 40 L260 40 L265 22 Z" fill="rgba(0,255,136,0.1)"/>
                    <!-- Phares -->
                    <ellipse cx="60" cy="80" rx="10" ry="8"/>
                    <ellipse cx="340" cy="80" rx="10" ry="8"/>
                </svg>
                
                <!-- Indicateur d'angle -->
                <div class="angle-indicator" id="angleIndicator">0° - Face avant</div>
                
                <!-- Instructions -->
                <div class="instructions" id="instructions">
                    Aligne la voiture avec la silhouette
                </div>
                
                <!-- Counter -->
                <div class="capture-counter" id="captureCounter">0 / 36</div>
                
                <!-- Progress dots -->
                <div class="progress-360" id="progressDots"></div>
                
                <!-- Gallery preview -->
                <div class="gallery-preview" id="galleryPreview" style="display: none;">
                    <img id="lastCapture" src="" alt="Last">
                </div>
            </div>
            
            <!-- Mode buttons -->
            <div class="mode-selector">
                <button class="mode-btn active" data-mode="single">Photo</button>
                <button class="mode-btn" data-mode="360">360°</button>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" id="btnGallery">
                <svg viewBox="0 0 24 24"><path d="M22 16V4c0-1.1-.9-2-2-2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2zm-11-4l2.03 2.71L16 11l4 5H8l3-4zM2 6v14c0 1.1.9 2 2 2h14v-2H4V6H2z"/></svg>
                Galerie
            </button>
            
            <button class="btn-capture" id="btnCapture"></button>
            
            <button class="btn" id="btnProcess">
                <svg viewBox="0 0 24 24"><path d="M19 8l-4 4h3c0 3.31-2.69 6-6 6-1.01 0-1.97-.25-2.8-.7l-1.46 1.46C8.97 19.54 10.43 20 12 20c4.42 0 8-3.58 8-8h3l-4-4zM6 12c0-3.31 2.69-6 6-6 1.01 0 1.97.25 2.8.7l1.46-1.46C15.03 4.46 13.57 4 12 4c-4.42 0-8 3.58-8 8H1l4 4 4-4H6z"/></svg>
                Traiter
            </button>
        </div>
    </div>
    
    <!-- Loading -->
    <div class="loading-overlay" id="loading">
        <div class="spinner"></div>
        <p style="margin-top: 20px;">Traitement en cours...</p>
    </div>
    
    <!-- Flash -->
    <div class="flash" id="flash"></div>
    
    <canvas id="canvas" style="display: none;"></canvas>
    
    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const btnCapture = document.getElementById('btnCapture');
        const btnProcess = document.getElementById('btnProcess');
        const flash = document.getElementById('flash');
        const loading = document.getElementById('loading');
        const angleIndicator = document.getElementById('angleIndicator');
        const instructions = document.getElementById('instructions');
        const captureCounter = document.getElementById('captureCounter');
        const progressDots = document.getElementById('progressDots');
        const galleryPreview = document.getElementById('galleryPreview');
        const lastCapture = document.getElementById('lastCapture');
        
        let captures = [];
        let currentAngleIndex = 0;
        let mode = 'single'; // 'single' ou '360'
        
        const ANGLES = [
            {deg: 0, label: 'Face avant'},
            {deg: 45, label: 'Avant 3/4 droit'},
            {deg: 90, label: 'Profil droit'},
            {deg: 135, label: 'Arriere 3/4 droit'},
            {deg: 180, label: 'Face arriere'},
            {deg: 225, label: 'Arriere 3/4 gauche'},
            {deg: 270, label: 'Profil gauche'},
            {deg: 315, label: 'Avant 3/4 gauche'}
        ];
        
        // Init progress dots pour mode 360 (8 angles principaux)
        function initProgressDots() {
            progressDots.innerHTML = '';
            ANGLES.forEach((angle, i) => {
                const dot = document.createElement('div');
                dot.className = 'progress-dot' + (i === 0 ? ' current' : '');
                dot.title = angle.label;
                progressDots.appendChild(dot);
            });
        }
        
        // Update UI
        function updateUI() {
            const angle = ANGLES[currentAngleIndex];
            angleIndicator.textContent = `${angle.deg}° - ${angle.label}`;
            captureCounter.textContent = `${captures.length} / ${ANGLES.length}`;
            
            // Update progress dots
            document.querySelectorAll('.progress-dot').forEach((dot, i) => {
                dot.classList.remove('current', 'captured');
                if (i < captures.length) dot.classList.add('captured');
                if (i === currentAngleIndex) dot.classList.add('current');
            });
            
            // Update instructions
            if (mode === '360') {
                if (captures.length === 0) {
                    instructions.textContent = 'Commence par la face avant de la voiture';
                } else if (captures.length < ANGLES.length) {
                    instructions.textContent = `Tourne vers ${ANGLES[currentAngleIndex].label}`;
                } else {
                    instructions.textContent = 'Capture complete ! Clique sur Traiter';
                }
            } else {
                instructions.textContent = 'Aligne la voiture avec la silhouette';
            }
        }
        
        // Init camera
        async function initCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: 'environment',
                        width: { ideal: 1920 },
                        height: { ideal: 1080 }
                    },
                    audio: false
                });
                video.srcObject = stream;
                
                video.onloadedmetadata = () => {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                };
            } catch (err) {
                alert('Erreur camera: ' + err.message);
            }
        }
        
        // Capture photo
        function capturePhoto() {
            // Flash effect
            flash.classList.add('active');
            setTimeout(() => flash.classList.remove('active'), 200);
            
            // Capture
            ctx.drawImage(video, 0, 0);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
            
            captures.push({
                angle: ANGLES[currentAngleIndex].deg,
                image: dataUrl
            });
            
            // Update preview
            lastCapture.src = dataUrl;
            galleryPreview.style.display = 'block';
            
            // Next angle
            if (mode === '360' && currentAngleIndex < ANGLES.length - 1) {
                currentAngleIndex++;
            }
            
            updateUI();
            
            // Vibration feedback
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
        
        // Process captures
        async function processCaptures() {
            if (captures.length === 0) {
                alert('Aucune photo a traiter');
                return;
            }
            
            loading.classList.add('show');
            
            try {
                const response = await fetch('/process_captures', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ captures: captures })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show results
                alert(`${data.count} photos traitees avec succes!`);
                
                // Reset
                captures = [];
                currentAngleIndex = 0;
                updateUI();
                
            } catch (err) {
                alert('Erreur: ' + err.message);
            }
            
            loading.classList.remove('show');
        }
        
        // Mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                mode = btn.dataset.mode;
                
                // Reset
                captures = [];
                currentAngleIndex = 0;
                
                // Show/hide progress
                progressDots.style.display = mode === '360' ? 'flex' : 'none';
                
                updateUI();
            });
        });
        
        // Event listeners
        btnCapture.addEventListener('click', capturePhoto);
        btnProcess.addEventListener('click', processCaptures);
        
        // Init
        initCamera();
        initProgressDots();
        updateUI();
        progressDots.style.display = 'none'; // Hidden in single mode
    </script>
</body>
</html>'''


@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Spyne Camera",
        "short_name": "Spyne",
        "start_url": "/",
        "display": "fullscreen",
        "orientation": "landscape",
        "background_color": "#000000",
        "theme_color": "#00ff88",
        "icons": [
            {
                "src": "/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    })


@app.route('/process_captures', methods=['POST'])
def process_captures():
    try:
        data = request.json
        captures = data.get('captures', [])
        
        if not captures:
            return jsonify({'error': 'Aucune capture'}), 400
        
        print(f"\nTraitement de {len(captures)} captures...")
        
        results = []
        for i, capture in enumerate(captures):
            print(f"  Processing {i+1}/{len(captures)}...")
            
            # Decode base64
            image_data = capture['image']
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            
            # Segmentation
            result = remove(pil_image, session=SESSION)
            
            # Save
            filename = f"capture_{capture['angle']:03d}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            result.save(filepath, 'PNG')
            
            results.append(filename)
        
        print(f"Done! {len(results)} images saved to {OUTPUT_DIR}")
        
        return jsonify({
            'success': True,
            'count': len(results),
            'files': results
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Port from environment (Railway) or default 5000
    port = int(os.environ.get('PORT', 5000))
    
    print("\n" + "="*50)
    print("Spyne Camera - Mobile App")
    print("="*50)
    print(f"\nCaptures: {OUTPUT_DIR}")
    print(f"\nRunning on port: {port}")
    print("Ctrl+C pour arreter\n")
    app.run(host='0.0.0.0', port=port, debug=False)

