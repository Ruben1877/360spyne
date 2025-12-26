"""
Serveur de demo COMPLET - Clone Spyne
Utilise une vraie image de studio avec plateau tournant
Lance: python demo_server.py
Ouvre: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
import io
import numpy as np
from PIL import Image
import cv2

# Installer les dependances si necessaire
try:
    from rembg import remove, new_session
except ImportError:
    os.system("pip install rembg[cpu] flask flask-cors")
    from rembg import remove, new_session

# Importer le module studio
from studio_background import StudioBackground

app = Flask(__name__)
CORS(app)

# Charger le modele une seule fois
print("Chargement du modele ISNet...")
SESSION = new_session("isnet-general-use")
print("Modele charge!")

# Charger le fond studio
BACKGROUNDS_DIR = os.path.join(os.path.dirname(__file__), "backgrounds")
DEFAULT_BG = os.path.join(BACKGROUNDS_DIR, "studio_real.jpg")

print(f"Fond studio: {DEFAULT_BG}")
STUDIO = StudioBackground(DEFAULT_BG)

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clone Spyne - Studio Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Satoshi:wght@400;500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --emerald: #10b981;
            --emerald-dark: #059669;
            --red: #ef4444;
            --blue: #3b82f6;
            --slate-50: #f8fafc;
            --slate-100: #f1f5f9;
            --slate-200: #e2e8f0;
            --slate-300: #cbd5e1;
            --slate-400: #94a3b8;
            --slate-500: #64748b;
            --slate-600: #475569;
            --slate-700: #334155;
            --slate-800: #1e293b;
            --slate-900: #0f172a;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--slate-900);
            color: var(--slate-100);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        h1 {
            font-family: 'Satoshi', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
            margin-bottom: 0.5rem;
        }
        
        h1 i { color: var(--emerald); margin-right: 0.5rem; }
        
        .subtitle { color: var(--slate-400); font-size: 1.1rem; }
        
        .main-grid {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 900px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        
        .sidebar {
            background: var(--slate-800);
            border-radius: 6px;
            padding: 1.5rem;
        }
        
        .sidebar h3 {
            font-family: 'Satoshi', sans-serif;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .sidebar h3 i { color: var(--emerald); }
        
        .upload-zone {
            border: 2px dashed var(--slate-600);
            border-radius: 6px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 1.5rem;
        }
        
        .upload-zone:hover, .upload-zone.dragover {
            border-color: var(--emerald);
            background: rgba(16, 185, 129, 0.1);
        }
        
        .upload-zone i { font-size: 2rem; color: var(--slate-500); margin-bottom: 0.5rem; }
        .upload-zone p { color: var(--slate-400); font-size: 0.875rem; }
        
        #fileInput { display: none; }
        
        .option-group {
            margin-bottom: 1.5rem;
        }
        
        .option-group label {
            display: block;
            color: var(--slate-300);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }
        
        .option-group input[type="range"] {
            width: 100%;
            height: 6px;
            -webkit-appearance: none;
            background: var(--slate-600);
            border-radius: 3px;
            cursor: pointer;
        }
        
        .option-group input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: var(--emerald);
            border-radius: 50%;
            cursor: pointer;
        }
        
        .range-value {
            text-align: right;
            font-size: 0.75rem;
            color: var(--slate-400);
            margin-top: 0.25rem;
        }
        
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--slate-700);
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            font-size: 0.875rem;
            cursor: pointer;
        }
        
        .checkbox-item input { accent-color: var(--emerald); }
        
        .btn-process {
            width: 100%;
            padding: 1rem;
            background: var(--emerald);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .btn-process:hover { background: var(--emerald-dark); }
        .btn-process:disabled { background: var(--slate-600); cursor: not-allowed; }
        
        .results-area {
            background: var(--slate-800);
            border-radius: 6px;
            padding: 1.5rem;
        }
        
        .result-main {
            margin-bottom: 1.5rem;
        }
        
        .result-main img {
            width: 100%;
            max-height: 500px;
            object-fit: contain;
            border-radius: 6px;
            background: #1a1a1a;
        }
        
        .result-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .result-actions a {
            flex: 1;
            text-align: center;
            padding: 0.75rem;
            background: var(--emerald);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        .result-actions a:hover { background: var(--emerald-dark); }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }
        
        .result-thumb {
            background: var(--slate-700);
            border-radius: 6px;
            overflow: hidden;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .result-thumb:hover { transform: scale(1.02); }
        
        .result-thumb img {
            width: 100%;
            height: 100px;
            object-fit: contain;
            background: repeating-conic-gradient(var(--slate-600) 0% 25%, var(--slate-700) 0% 50%) 50% / 12px 12px;
        }
        
        .result-thumb p {
            padding: 0.5rem;
            font-size: 0.75rem;
            color: var(--slate-400);
            text-align: center;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 3rem;
        }
        
        .loading.show { display: block; }
        
        .loading i {
            font-size: 3rem;
            color: var(--emerald);
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .loading p { margin-top: 1rem; color: var(--slate-400); }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--slate-700);
            border-radius: 6px;
        }
        
        .stat { text-align: center; }
        .stat-value { font-family: 'Satoshi', sans-serif; font-size: 1.25rem; font-weight: 700; color: var(--emerald); }
        .stat-label { font-size: 0.75rem; color: var(--slate-400); }
        
        .preview-original {
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .preview-original img {
            max-width: 100%;
            max-height: 120px;
            border-radius: 6px;
        }
        
        .hidden { display: none !important; }
        
        .info-box {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid var(--emerald);
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            font-size: 0.875rem;
            color: var(--slate-300);
        }
        
        .info-box i { color: var(--emerald); margin-right: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fas fa-car"></i> Clone Spyne Studio</h1>
            <p class="subtitle">Fond studio reel avec plateau tournant</p>
        </header>
        
        <div class="main-grid">
            <div class="sidebar">
                <h3><i class="fas fa-cog"></i> Parametres</h3>
                
                <div class="info-box">
                    <i class="fas fa-info-circle"></i>
                    Utilise une vraie photo de studio avec plateau tournant pour un rendu ultra-realiste.
                </div>
                
                <div class="upload-zone" id="uploadZone">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <p>Glisse une photo de voiture</p>
                    <input type="file" id="fileInput" accept="image/*">
                </div>
                
                <div class="preview-original hidden" id="previewOriginal">
                    <img id="previewImg" src="" alt="Preview">
                </div>
                
                <div class="option-group">
                    <label><i class="fas fa-expand-arrows-alt"></i> Taille voiture</label>
                    <input type="range" id="carScale" min="30" max="80" value="55">
                    <div class="range-value" id="carScaleValue">55%</div>
                </div>
                
                <div class="option-group">
                    <label><i class="fas fa-moon"></i> Intensite ombre</label>
                    <input type="range" id="shadowIntensity" min="0" max="100" value="40">
                    <div class="range-value" id="shadowValue">40%</div>
                </div>
                
                <div class="option-group">
                    <label><i class="fas fa-clone"></i> Intensite reflet</label>
                    <input type="range" id="reflectionIntensity" min="0" max="50" value="15">
                    <div class="range-value" id="reflectionValue">15%</div>
                </div>
                
                <div class="checkbox-group">
                    <label class="checkbox-item">
                        <input type="checkbox" id="optShadow" checked> Ombre
                    </label>
                    <label class="checkbox-item">
                        <input type="checkbox" id="optReflection" checked> Reflet
                    </label>
                </div>
                
                <button class="btn-process" id="btnProcess" disabled>
                    <i class="fas fa-magic"></i> Traiter l'image
                </button>
            </div>
            
            <div class="results-area">
                <div class="loading" id="loading">
                    <i class="fas fa-spinner"></i>
                    <p>Traitement en cours...</p>
                </div>
                
                <div class="hidden" id="resultsContainer">
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value" id="statTime">-</div>
                            <div class="stat-label">Temps</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="statSize">-</div>
                            <div class="stat-label">Resolution</div>
                        </div>
                    </div>
                    
                    <div class="result-main">
                        <img id="imgFinal" src="" alt="Resultat">
                        <div class="result-actions">
                            <a href="#" id="downloadFinal"><i class="fas fa-download"></i> Telecharger HD</a>
                        </div>
                    </div>
                    
                    <div class="results-grid">
                        <div class="result-thumb" onclick="showImage('imgOriginal')">
                            <img id="imgOriginal" src="" alt="Original">
                            <p>Original</p>
                        </div>
                        <div class="result-thumb" onclick="showImage('imgMask')">
                            <img id="imgMask" src="" alt="Masque">
                            <p>Masque</p>
                        </div>
                        <div class="result-thumb" onclick="showImage('imgNobg')">
                            <img id="imgNobg" src="" alt="Sans fond">
                            <p>Sans fond</p>
                        </div>
                        <div class="result-thumb" onclick="showImage('imgBg')">
                            <img id="imgBg" src="" alt="Studio">
                            <p>Studio</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const btnProcess = document.getElementById('btnProcess');
        const loading = document.getElementById('loading');
        const resultsContainer = document.getElementById('resultsContainer');
        const previewOriginal = document.getElementById('previewOriginal');
        const previewImg = document.getElementById('previewImg');
        
        let currentImage = null;
        
        // Upload handlers
        uploadZone.addEventListener('click', () => fileInput.click());
        
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                loadImage(file);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) loadImage(file);
        });
        
        function loadImage(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                currentImage = e.target.result;
                previewImg.src = currentImage;
                previewOriginal.classList.remove('hidden');
                btnProcess.disabled = false;
                resultsContainer.classList.add('hidden');
            };
            reader.readAsDataURL(file);
        }
        
        // Range sliders
        document.getElementById('carScale').addEventListener('input', (e) => {
            document.getElementById('carScaleValue').textContent = e.target.value + '%';
        });
        
        document.getElementById('shadowIntensity').addEventListener('input', (e) => {
            document.getElementById('shadowValue').textContent = e.target.value + '%';
        });
        
        document.getElementById('reflectionIntensity').addEventListener('input', (e) => {
            document.getElementById('reflectionValue').textContent = e.target.value + '%';
        });
        
        // Show full image
        function showImage(id) {
            document.getElementById('imgFinal').src = document.getElementById(id).src;
        }
        
        // Process button
        btnProcess.addEventListener('click', processImage);
        
        async function processImage() {
            if (!currentImage) return;
            
            loading.classList.add('show');
            resultsContainer.classList.add('hidden');
            btnProcess.disabled = true;
            
            const startTime = Date.now();
            
            const options = {
                image: currentImage,
                car_scale: parseInt(document.getElementById('carScale').value) / 100,
                shadow_opacity: parseInt(document.getElementById('shadowIntensity').value) / 100,
                reflection_opacity: parseInt(document.getElementById('reflectionIntensity').value) / 100,
                add_shadow: document.getElementById('optShadow').checked,
                add_reflection: document.getElementById('optReflection').checked
            };
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(options)
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Display results
                document.getElementById('imgOriginal').src = currentImage;
                document.getElementById('imgMask').src = data.mask;
                document.getElementById('imgNobg').src = data.nobg;
                document.getElementById('imgBg').src = data.background;
                document.getElementById('imgFinal').src = data.final;
                
                // Download link
                document.getElementById('downloadFinal').href = data.final;
                document.getElementById('downloadFinal').download = 'spyne_studio_result.png';
                
                // Stats
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
                document.getElementById('statTime').textContent = elapsed + 's';
                document.getElementById('statSize').textContent = data.size;
                
                loading.classList.remove('show');
                resultsContainer.classList.remove('hidden');
                
            } catch (err) {
                alert('Erreur: ' + err.message);
                loading.classList.remove('show');
            }
            
            btnProcess.disabled = false;
        }
    </script>
</body>
</html>'''


@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'Pas d\'image'}), 400
        
        # Options
        car_scale = data.get('car_scale', 0.55)
        shadow_opacity = data.get('shadow_opacity', 0.4)
        reflection_opacity = data.get('reflection_opacity', 0.15)
        add_shadow = data.get('add_shadow', True)
        add_reflection = data.get('add_reflection', True)
        
        # Decode base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        w, h = pil_image.size
        
        print(f"Processing {w}x{h}...")
        
        # ===== STEP 1: SEGMENTATION =====
        print("  1. Segmentation...")
        mask_pil = remove(pil_image, session=SESSION, only_mask=True)
        nobg_pil = remove(pil_image, session=SESSION)
        
        mask_np = np.array(mask_pil)
        image_np = np.array(pil_image)
        
        # Convert to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # ===== STEP 2: COMPOSITE SUR STUDIO =====
        print("  2. Composite sur studio...")
        
        # Recharger le fond studio a chaque fois (pour eviter les modifications persistantes)
        studio = StudioBackground(DEFAULT_BG)
        
        final_bgr = studio.composite_car_on_studio(
            image_bgr,
            mask_np,
            add_shadow=add_shadow,
            add_reflection=add_reflection,
            shadow_opacity=shadow_opacity,
            reflection_opacity=reflection_opacity,
            car_scale=car_scale
        )
        
        # Convertir en RGB
        final_rgb = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB)
        bg_rgb = cv2.cvtColor(studio.background, cv2.COLOR_BGR2RGB)
        
        final_size = f"{studio.bg_width}x{studio.bg_height}"
        
        print("  Done!")
        
        # Convert to base64
        def to_base64(img, format='PNG'):
            if isinstance(img, np.ndarray):
                img = Image.fromarray(img)
            buffer = io.BytesIO()
            if format == 'JPEG':
                img = img.convert('RGB')
            img.save(buffer, format=format, quality=95)
            return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'mask': to_base64(mask_pil),
            'nobg': to_base64(nobg_pil),
            'background': to_base64(bg_rgb, 'JPEG'),
            'final': to_base64(final_rgb, 'JPEG'),
            'size': final_size
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Clone Spyne - Studio Pro")
    print("="*50)
    print("\nFond studio reel avec plateau tournant")
    print(f"Background: {DEFAULT_BG}")
    print("\nOuvre: http://localhost:5000")
    print("Ctrl+C pour arreter\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
