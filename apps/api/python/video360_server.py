"""
VIDEO 360 - Clone Spyne
=======================
Upload une video, extrait 36 frames, retire le fond, cree une vue 360.
Lance: python video360_server.py
Ouvre: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import io
import numpy as np
from PIL import Image
import cv2
import tempfile
import shutil
from pathlib import Path

# Installer les dependances si necessaire
try:
    from rembg import remove, new_session
except ImportError:
    os.system("pip install rembg[cpu] flask flask-cors")
    from rembg import remove, new_session

app = Flask(__name__)
CORS(app)

# Charger le modele une seule fois
print("Chargement du modele ISNet...")
SESSION = new_session("isnet-general-use")
print("Modele charge!")

# Dossier pour les outputs
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output_360")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_frames(video_path: str, num_frames: int = 36) -> list:
    """
    Extrait N frames uniformement reparties d'une video.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        cap.release()
        raise ValueError("Video vide ou illisible")
    
    # Calculer les indices des frames a extraire
    if total_frames <= num_frames:
        indices = list(range(total_frames))
    else:
        indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
    
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convertir BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
    
    cap.release()
    print(f"  Extrait {len(frames)} frames sur {total_frames} total")
    return frames


def segment_frames(frames: list, session, mode: str = "transparent", ai_prompt: str = "", ai_preset: str = "studio_white") -> list:
    """
    Segmente chaque frame pour retirer le fond.
    
    Modes:
    - "transparent": fond transparent (RGBA)
    - "inpaint": genere le fond localement (gratuit)
    - "ai_inpaint": genere le fond avec IA (Replicate)
    - "white": fond blanc
    - "studio": fond gris degrade studio
    """
    segmented = []
    total = len(frames)
    
    for i, frame in enumerate(frames):
        print(f"  Segmentation frame {i+1}/{total}...", end='\r')
        
        # Convertir en PIL Image
        pil_img = Image.fromarray(frame)
        
        # Obtenir le masque
        mask_pil = remove(pil_img, session=session, only_mask=True)
        mask_np = np.array(mask_pil)
        
        if mode == "transparent":
            # Fond transparent
            result = remove(pil_img, session=session)
            
        elif mode == "inpaint":
            # Inpainting local - generer le fond (gratuit)
            result = inpaint_background(frame, mask_np)
            result = Image.fromarray(result)
            
        elif mode == "ai_inpaint":
            # Inpainting IA - generer le fond avec Google Imagen 4
            print(f"  [Imagen 4] Frame {i+1}/{total}...")
            result = inpaint_with_ai(frame, mask_np, prompt=ai_prompt, preset=ai_preset)
            result = Image.fromarray(result)
            
        elif mode == "white":
            # Fond blanc
            result = remove(pil_img, session=session, bgcolor=(255, 255, 255, 255))
            
        elif mode == "studio":
            # Fond studio gris degrade
            nobg = remove(pil_img, session=session)
            result = add_studio_background(nobg)
        
        else:
            result = remove(pil_img, session=session)
        
        segmented.append(result)
    
    print(f"  Segmentation terminee: {total} frames")
    return segmented


def inpaint_background(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Inpainting local avec OpenCV (rapide, gratuit).
    """
    h, w = frame.shape[:2]
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    kernel = np.ones((10, 10), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations=3)
    
    clean_background = cv2.inpaint(frame_bgr, mask_dilated, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
    
    mask_3ch = np.stack([mask, mask, mask], axis=2) / 255.0
    result_bgr = (clean_background * (1 - mask_3ch) + frame_bgr * mask_3ch).astype(np.uint8)
    
    result = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)
    return result


# =============================================================================
# PROMPTS OPTIMISES POUR FONDS AUTOMOBILES - IMAGEN 4
# =============================================================================
# Ces prompts sont engineeres pour:
# - Generer des fonds SANS voiture (le sujet sera superpose apres)
# - Maintenir une coherence visuelle sur 36+ frames
# - Creer un eclairage realiste de studio photo automobile
# =============================================================================

BG_PRESETS = {
    "studio_white": """
        Professional automotive photography studio environment, EMPTY SCENE WITH NO VEHICLE NO CAR NO AUTOMOBILE in frame.
        Clean infinite white cyclorama wall curving seamlessly into polished light gray epoxy floor.
        Soft diffused overhead lighting from large softboxes creating gentle gradients.
        Subtle floor reflection, minimal shadows. Commercial car photography backdrop.
        Ultra clean minimalist space, no objects, no people, no distractions.
        Photorealistic, 8K quality, professional product photography lighting.
        The center of the frame is completely empty and clear for product placement.
    """,
    
    "studio_dark": """
        Luxury dark automotive photography studio, EMPTY SCENE WITH NO VEHICLE NO CAR NO AUTOMOBILE visible.
        Dramatic black infinity cove background with polished dark concrete or black epoxy reflective floor.
        Cinematic rim lighting from sides, subtle blue accent lights in background.
        High contrast dramatic lighting setup, deep shadows, elegant atmosphere.
        Premium car reveal aesthetic, spotlight ready position in center.
        Empty center stage area, moody automotive commercial environment.
        Photorealistic, 8K, luxury brand photography style, no objects in scene.
    """,
    
    "showroom": """
        Modern luxury car dealership showroom interior, EMPTY FLOOR SPACE WITH NO VEHICLES NO CARS displayed.
        Clean polished white marble or light terrazzo floor with subtle reflections.
        Large floor-to-ceiling windows with soft natural daylight, modern architectural ceiling.
        Minimalist contemporary interior design, neutral white and gray tones.
        Professional automotive retail environment, empty display area in center.
        Soft ambient lighting, no furniture, no people, clear open space.
        Photorealistic interior photography, architectural visualization quality.
    """,
    
    "outdoor": """
        Clean outdoor automotive photography location, EMPTY SCENE NO VEHICLE NO CAR in frame.
        Smooth gray asphalt or concrete surface, overcast sky providing soft even lighting.
        Neutral industrial or urban background slightly out of focus.
        Professional outdoor car photoshoot environment, flat open area.
        No harsh shadows, diffused natural daylight, clean minimalist surroundings.
        Empty center area ready for vehicle placement, no people or objects.
        Photorealistic outdoor photography, commercial automotive advertising style.
    """,
    
    "garage": """
        Premium modern garage or automotive workshop environment, EMPTY BAY WITH NO VEHICLE NO CAR inside.
        Clean polished concrete floor with subtle oil-resistant coating, light gray tones.
        Industrial chic aesthetic with exposed ceiling, professional LED lighting.
        Tool cabinets and equipment visible on edges but center completely clear.
        Automotive enthusiast space, high-end detailing studio atmosphere.
        Empty lift area or display zone in center, clean and organized.
        Photorealistic, professional automotive photography, workshop setting.
    """
}


def get_optimized_prompt(preset: str, custom_prompt: str = "") -> str:
    """
    Retourne un prompt optimise pour Imagen 4.
    Ajoute des instructions de coherence et de qualite.
    """
    if preset == "custom" and custom_prompt:
        base_prompt = custom_prompt
    else:
        base_prompt = BG_PRESETS.get(preset, BG_PRESETS["studio_white"])
    
    # Nettoyer et formater
    base_prompt = " ".join(base_prompt.split())
    
    # Ajouter des instructions de coherence
    consistency_suffix = """
        Consistent lighting direction and color temperature throughout.
        Static camera angle, fixed perspective, no motion blur.
        Maintain exact same environment style and mood.
        CRITICAL: Absolutely no cars, vehicles, automobiles, or any transportation in the image.
        The center must be empty and clear.
    """
    
    return f"{base_prompt} {' '.join(consistency_suffix.split())}"


def inpaint_with_ai(frame: np.ndarray, mask: np.ndarray, prompt: str = "", preset: str = "studio_white") -> np.ndarray:
    """
    Genere un fond pro avec Google Imagen 4 via Replicate.
    
    1. Genere un fond studio avec Imagen 4 (prompt optimise)
    2. Place la voiture originale sur ce fond genere
    
    Les prompts sont engineeres pour:
    - Ne JAMAIS generer de voiture
    - Maintenir une coherence sur toutes les frames
    - Creer un eclairage studio professionnel
    """
    try:
        import replicate
    except ImportError:
        print("  Replicate non installe, fallback sur OpenCV")
        return inpaint_background(frame, mask)
    
    # Verifier la cle API
    api_token = os.environ.get('REPLICATE_API_TOKEN')
    if not api_token:
        print("  REPLICATE_API_TOKEN non defini, fallback sur OpenCV")
        return inpaint_background(frame, mask)
    
    h, w = frame.shape[:2]
    
    # Determiner le ratio d'aspect
    if w > h:
        aspect = "16:9"
    elif h > w:
        aspect = "9:16"
    else:
        aspect = "1:1"
    
    # Obtenir le prompt optimise
    optimized_prompt = get_optimized_prompt(preset, prompt)
    
    try:
        # Generer le fond avec Google Imagen 4
        print(f"    Imagen 4 [{preset}]...")
        
        output = replicate.run(
            "google/imagen-4",
            input={
                "prompt": optimized_prompt,
                "aspect_ratio": aspect,
                "safety_filter_level": "block_only_high"
            }
        )
        
        # Telecharger le resultat
        if output:
            import urllib.request
            
            # Determiner l'URL selon le type de retour
            if hasattr(output, 'read'):
                # C'est un fichier directement
                result_data = output.read()
            else:
                # C'est une URL (string)
                url = str(output)
                print(f"    Downloading from: {url[:50]}...")
                with urllib.request.urlopen(url) as response:
                    result_data = response.read()
            
            result_pil = Image.open(io.BytesIO(result_data)).convert('RGB')
            
            # Redimensionner le fond a la taille de l'image originale
            result_pil = result_pil.resize((w, h), Image.LANCZOS)
            generated_bg = np.array(result_pil)
            
            # Placer la voiture originale sur le fond genere
            # Adoucir les bords du masque pour une meilleure integration
            mask_float = mask.astype(np.float32) / 255.0
            mask_blurred = cv2.GaussianBlur(mask_float, (5, 5), 0)
            mask_3ch = np.stack([mask_blurred, mask_blurred, mask_blurred], axis=2)
            
            # Composer
            result = (generated_bg * (1 - mask_3ch) + frame * mask_3ch).astype(np.uint8)
            
            print(f"    Imagen 4 OK!")
            return result
        
    except Exception as e:
        print(f"  Erreur Imagen 4: {e}, fallback sur OpenCV")
        import traceback
        traceback.print_exc()
    
    return inpaint_background(frame, mask)


def add_studio_background(nobg_image: Image.Image) -> Image.Image:
    """
    Ajoute un fond studio gris degrade derriere la voiture.
    """
    w, h = nobg_image.size
    
    # Creer un fond gris degrade
    background = np.zeros((h, w, 3), dtype=np.uint8)
    
    for y in range(h):
        # Degrade du haut (clair) vers le bas (plus fonce)
        t = y / h
        gray = int(220 - t * 40)  # 220 -> 180
        background[y, :] = [gray, gray, gray]
    
    # Ajouter une vignette subtile
    center_x, center_y = w // 2, h // 2
    max_dist = np.sqrt(center_x**2 + center_y**2)
    
    for y in range(h):
        for x in range(w):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            vignette = 1 - (dist / max_dist) * 0.15
            background[y, x] = np.clip(background[y, x] * vignette, 0, 255).astype(np.uint8)
    
    bg_pil = Image.fromarray(background)
    
    # Composer la voiture sur le fond
    bg_pil.paste(nobg_image, (0, 0), nobg_image)
    
    return bg_pil


def save_frames(frames: list, output_dir: str, prefix: str = "frame", mode: str = "transparent") -> list:
    """
    Sauvegarde les frames.
    PNG pour transparent, JPEG pour les autres (plus leger).
    Retourne la liste des chemins.
    """
    paths = []
    ext = "png" if mode == "transparent" else "jpg"
    
    for i, frame in enumerate(frames):
        filename = f"{prefix}_{i:03d}.{ext}"
        filepath = os.path.join(output_dir, filename)
        
        if ext == "jpg":
            # Convertir RGBA en RGB pour JPEG
            if frame.mode == 'RGBA':
                rgb_frame = Image.new('RGB', frame.size, (255, 255, 255))
                rgb_frame.paste(frame, mask=frame.split()[3])
                frame = rgb_frame
            frame.save(filepath, "JPEG", quality=95)
        else:
            frame.save(filepath, "PNG")
        
        paths.append(filename)
    return paths


@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clone Spyne - Video 360</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --success: #10b981;
            --dark: #0f0f0f;
            --dark-2: #1a1a1a;
            --dark-3: #262626;
            --gray: #737373;
            --light: #fafafa;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Space Grotesk', sans-serif;
            background: var(--dark);
            color: var(--light);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--primary), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle { color: var(--gray); font-size: 1.1rem; }
        
        .upload-section {
            background: var(--dark-2);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .upload-zone {
            border: 2px dashed var(--gray);
            border-radius: 12px;
            padding: 4rem 2rem;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-zone:hover, .upload-zone.dragover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
        }
        
        .upload-zone i {
            font-size: 4rem;
            color: var(--primary);
            margin-bottom: 1rem;
        }
        
        .upload-zone h3 { font-size: 1.5rem; margin-bottom: 0.5rem; }
        .upload-zone p { color: var(--gray); }
        
        #fileInput { display: none; }
        
        .options {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }
        
        .option {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .option label { color: var(--gray); }
        
        .option input[type="number"] {
            width: 60px;
            padding: 0.5rem;
            background: var(--dark-3);
            border: 1px solid var(--gray);
            border-radius: 6px;
            color: var(--light);
            font-family: inherit;
        }
        
        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover { background: var(--primary-dark); }
        .btn-primary:disabled { background: var(--gray); cursor: not-allowed; }
        
        .btn-success {
            background: var(--success);
            color: white;
        }
        
        .progress-section {
            display: none;
            background: var(--dark-2);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        
        .progress-section.show { display: block; }
        
        .progress-bar {
            height: 8px;
            background: var(--dark-3);
            border-radius: 4px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--success));
            width: 0%;
            transition: width 0.3s;
        }
        
        .progress-text { color: var(--gray); text-align: center; }
        
        .viewer-section {
            display: none;
            background: var(--dark-2);
            border-radius: 16px;
            padding: 2rem;
        }
        
        .viewer-section.show { display: block; }
        
        .viewer-container {
            position: relative;
            background: repeating-conic-gradient(var(--dark-3) 0% 25%, var(--dark-2) 0% 50%) 50% / 20px 20px;
            border-radius: 12px;
            overflow: hidden;
            aspect-ratio: 16/9;
            max-height: 500px;
            margin: 0 auto;
            cursor: grab;
        }
        
        .viewer-container:active { cursor: grabbing; }
        
        .viewer-container img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            user-select: none;
            -webkit-user-drag: none;
        }
        
        .viewer-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .frame-slider {
            flex: 1;
            max-width: 400px;
            -webkit-appearance: none;
            height: 6px;
            background: var(--dark-3);
            border-radius: 3px;
            cursor: pointer;
        }
        
        .frame-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            background: var(--primary);
            border-radius: 50%;
            cursor: pointer;
        }
        
        .frame-info {
            color: var(--gray);
            min-width: 100px;
            text-align: center;
        }
        
        .autoplay-btn {
            padding: 0.75rem 1.5rem;
            background: var(--dark-3);
            border: 1px solid var(--gray);
            border-radius: 8px;
            color: var(--light);
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .autoplay-btn:hover { border-color: var(--primary); }
        .autoplay-btn.playing { background: var(--primary); border-color: var(--primary); }
        
        .download-section {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-bottom: 1.5rem;
        }
        
        .stat { text-align: center; }
        .stat-value { font-size: 2rem; font-weight: 700; color: var(--primary); }
        .stat-label { color: var(--gray); font-size: 0.875rem; }
        
        .instructions {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid var(--primary);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
            font-size: 0.875rem;
            color: var(--gray);
        }
        
        .instructions i { color: var(--primary); margin-right: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><i class="fas fa-sync-alt"></i> Video 360</h1>
            <p class="subtitle">Upload une video, obtiens une vue 360 sans fond</p>
        </header>
        
        <div class="upload-section" id="uploadSection">
            <div class="upload-zone" id="uploadZone">
                <i class="fas fa-video"></i>
                <h3>Glisse ta video ici</h3>
                <p>ou clique pour parcourir (MP4, MOV, AVI)</p>
                <input type="file" id="fileInput" accept="video/*">
            </div>
            
            <div class="options">
                <div class="option">
                    <label>Frames:</label>
                    <input type="number" id="numFrames" value="36" min="8" max="72">
                </div>
                <div class="option">
                    <label>Fond:</label>
                    <select id="bgMode" style="padding: 0.5rem; background: var(--dark-3); border: 1px solid var(--gray); border-radius: 6px; color: var(--light); font-family: inherit;">
                        <option value="transparent">Transparent (PNG)</option>
                        <option value="inpaint">Inpaint local (gratuit)</option>
                        <option value="ai_inpaint">🤖 Imagen 4 (Google)</option>
                        <option value="studio">Studio gris</option>
                        <option value="white">Blanc</option>
                    </select>
                </div>
            </div>
            
            <div id="aiOptions" style="display: none; margin-top: 1rem; padding: 1rem; background: var(--dark-3); border-radius: 8px;">
                <label style="color: var(--gray); display: block; margin-bottom: 0.5rem;">Style de fond:</label>
                <select id="bgPreset" style="width: 100%; padding: 0.5rem; background: var(--dark); border: 1px solid var(--gray); border-radius: 6px; color: var(--light); font-family: inherit; margin-bottom: 0.75rem;">
                    <option value="studio_white">⬜ Studio Blanc Premium</option>
                    <option value="studio_dark">⬛ Studio Sombre Luxe</option>
                    <option value="showroom">🏢 Showroom Concession</option>
                    <option value="outdoor">🌤️ Exterieur Neutre</option>
                    <option value="garage">🔧 Garage Premium</option>
                    <option value="custom">✏️ Prompt personnalise</option>
                </select>
                
                <div id="customPromptBox" style="display: none;">
                    <label style="color: var(--gray); display: block; margin-bottom: 0.5rem; font-size: 0.875rem;">Prompt personnalise:</label>
                    <textarea id="aiPrompt" rows="3" style="width: 100%; padding: 0.5rem; background: var(--dark); border: 1px solid var(--gray); border-radius: 6px; color: var(--light); font-family: inherit; resize: vertical;"></textarea>
                </div>
                
                <p style="color: var(--gray); font-size: 0.75rem; margin-top: 0.5rem;">
                    💡 $0.04/image (~$1.44 pour 36 frames) • Fonds coherents et harmonises
                </p>
            </div>
            
            <div class="instructions">
                <i class="fas fa-info-circle"></i>
                Filme en tournant autour de la voiture (360°). La video sera decoupee en frames uniformement reparties.
            </div>
            
            <button class="btn btn-primary" id="btnProcess" style="margin-top: 1.5rem;" disabled>
                <i class="fas fa-magic"></i> Traiter la video
            </button>
        </div>
        
        <div class="progress-section" id="progressSection">
            <h3 style="text-align: center; margin-bottom: 1rem;">
                <i class="fas fa-cog fa-spin"></i> Traitement en cours...
            </h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <p class="progress-text" id="progressText">Preparation...</p>
        </div>
        
        <div class="viewer-section" id="viewerSection">
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="statFrames">36</div>
                    <div class="stat-label">Frames</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="statTime">-</div>
                    <div class="stat-label">Temps</div>
                </div>
            </div>
            
            <div class="viewer-container" id="viewerContainer">
                <img id="viewerImage" src="" alt="360 View" draggable="false">
            </div>
            
            <div class="viewer-controls">
                <button class="autoplay-btn" id="autoplayBtn">
                    <i class="fas fa-play"></i> Auto
                </button>
                <input type="range" class="frame-slider" id="frameSlider" min="0" max="35" value="0">
                <span class="frame-info" id="frameInfo">1 / 36</span>
            </div>
            
            <div class="download-section">
                <button class="btn btn-success" id="downloadAll">
                    <i class="fas fa-download"></i> Telecharger ZIP
                </button>
                <button class="btn btn-primary" id="newVideo">
                    <i class="fas fa-redo"></i> Nouvelle video
                </button>
            </div>
        </div>
    </div>
    
    <script>
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const btnProcess = document.getElementById('btnProcess');
        const progressSection = document.getElementById('progressSection');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const viewerSection = document.getElementById('viewerSection');
        const viewerImage = document.getElementById('viewerImage');
        const frameSlider = document.getElementById('frameSlider');
        const frameInfo = document.getElementById('frameInfo');
        const autoplayBtn = document.getElementById('autoplayBtn');
        const viewerContainer = document.getElementById('viewerContainer');
        
        let currentVideo = null;
        let frames = [];
        let currentFrame = 0;
        let isPlaying = false;
        let playInterval = null;
        let isDragging = false;
        let startX = 0;
        let startFrame = 0;
        
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
            if (file && file.type.startsWith('video/')) {
                loadVideo(file);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) loadVideo(file);
        });
        
        function loadVideo(file) {
            currentVideo = file;
            uploadZone.innerHTML = `
                <i class="fas fa-check-circle" style="color: var(--success);"></i>
                <h3>${file.name}</h3>
                <p>${(file.size / 1024 / 1024).toFixed(1)} MB</p>
            `;
            btnProcess.disabled = false;
        }
        
        // Show/hide AI options
        document.getElementById('bgMode').addEventListener('change', (e) => {
            const aiOptions = document.getElementById('aiOptions');
            aiOptions.style.display = e.target.value === 'ai_inpaint' ? 'block' : 'none';
        });
        
        // Show/hide custom prompt
        document.getElementById('bgPreset').addEventListener('change', (e) => {
            const customBox = document.getElementById('customPromptBox');
            customBox.style.display = e.target.value === 'custom' ? 'block' : 'none';
        });
        
        // Process button
        btnProcess.addEventListener('click', processVideo);
        
        async function processVideo() {
            if (!currentVideo) return;
            
            const numFrames = parseInt(document.getElementById('numFrames').value);
            
            progressSection.classList.add('show');
            viewerSection.classList.remove('show');
            btnProcess.disabled = true;
            
            progressFill.style.width = '10%';
            progressText.textContent = 'Upload de la video...';
            
            const startTime = Date.now();
            
            // Create FormData
            const formData = new FormData();
            formData.append('video', currentVideo);
            formData.append('num_frames', numFrames);
            formData.append('bg_mode', document.getElementById('bgMode').value);
            formData.append('bg_preset', document.getElementById('bgPreset').value);
            formData.append('ai_prompt', document.getElementById('aiPrompt').value || '');
            
            try {
                const response = await fetch('/process_video', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Store frames
                frames = data.frames;
                
                // Update UI
                document.getElementById('statFrames').textContent = frames.length;
                document.getElementById('statTime').textContent = ((Date.now() - startTime) / 1000).toFixed(1) + 's';
                
                frameSlider.max = frames.length - 1;
                frameSlider.value = 0;
                currentFrame = 0;
                updateViewer();
                
                progressSection.classList.remove('show');
                viewerSection.classList.add('show');
                
            } catch (err) {
                alert('Erreur: ' + err.message);
                progressSection.classList.remove('show');
            }
            
            btnProcess.disabled = false;
        }
        
        // Viewer controls
        function updateViewer() {
            if (frames.length > 0) {
                viewerImage.src = '/output_360/' + frames[currentFrame];
                frameInfo.textContent = `${currentFrame + 1} / ${frames.length}`;
                frameSlider.value = currentFrame;
            }
        }
        
        frameSlider.addEventListener('input', (e) => {
            currentFrame = parseInt(e.target.value);
            updateViewer();
        });
        
        // Autoplay
        autoplayBtn.addEventListener('click', () => {
            isPlaying = !isPlaying;
            if (isPlaying) {
                autoplayBtn.classList.add('playing');
                autoplayBtn.innerHTML = '<i class="fas fa-pause"></i> Stop';
                playInterval = setInterval(() => {
                    currentFrame = (currentFrame + 1) % frames.length;
                    updateViewer();
                }, 100);
            } else {
                autoplayBtn.classList.remove('playing');
                autoplayBtn.innerHTML = '<i class="fas fa-play"></i> Auto';
                clearInterval(playInterval);
            }
        });
        
        // Drag to rotate
        viewerContainer.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startFrame = currentFrame;
            if (isPlaying) {
                autoplayBtn.click();
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const deltaX = e.clientX - startX;
            const sensitivity = 5;
            const frameDelta = Math.round(deltaX / sensitivity);
            currentFrame = (startFrame + frameDelta) % frames.length;
            if (currentFrame < 0) currentFrame += frames.length;
            updateViewer();
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
        
        // Touch support
        viewerContainer.addEventListener('touchstart', (e) => {
            isDragging = true;
            startX = e.touches[0].clientX;
            startFrame = currentFrame;
        });
        
        document.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            const deltaX = e.touches[0].clientX - startX;
            const sensitivity = 5;
            const frameDelta = Math.round(deltaX / sensitivity);
            currentFrame = (startFrame + frameDelta) % frames.length;
            if (currentFrame < 0) currentFrame += frames.length;
            updateViewer();
        });
        
        document.addEventListener('touchend', () => {
            isDragging = false;
        });
        
        // Download ZIP
        document.getElementById('downloadAll').addEventListener('click', () => {
            window.location.href = '/download_zip';
        });
        
        // New video
        document.getElementById('newVideo').addEventListener('click', () => {
            location.reload();
        });
    </script>
</body>
</html>'''


@app.route('/output_360/<filename>')
def serve_frame(filename):
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/process_video', methods=['POST'])
def process_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Pas de video'}), 400
        
        video = request.files['video']
        num_frames = int(request.form.get('num_frames', 36))
        bg_mode = request.form.get('bg_mode', 'transparent')
        bg_preset = request.form.get('bg_preset', 'studio_white')
        ai_prompt = request.form.get('ai_prompt', '')
        
        print(f"\n{'='*50}")
        print(f"Processing video: {video.filename}")
        print(f"Frames demandes: {num_frames}")
        print(f"Mode fond: {bg_mode}")
        if bg_mode == 'ai_inpaint':
            print(f"Preset: {bg_preset}")
            if bg_preset == 'custom':
                print(f"Prompt: {ai_prompt[:50]}...")
        
        # Sauvegarder temporairement la video
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "input_video.mp4")
        video.save(video_path)
        
        # Nettoyer le dossier output
        for f in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, f))
        
        # 1. Extraire les frames
        print("1. Extraction des frames...")
        frames = extract_frames(video_path, num_frames)
        
        if len(frames) == 0:
            raise ValueError("Impossible d'extraire les frames")
        
        # 2. Segmenter (retirer le fond)
        print(f"2. Segmentation (mode: {bg_mode})...")
        segmented = segment_frames(frames, SESSION, mode=bg_mode, ai_prompt=ai_prompt, ai_preset=bg_preset)
        
        # 3. Sauvegarder les frames
        print("3. Sauvegarde...")
        filenames = save_frames(segmented, OUTPUT_DIR, "car360", mode=bg_mode)
        
        # Nettoyer
        shutil.rmtree(temp_dir)
        
        print(f"Termine! {len(filenames)} frames generees")
        print('='*50)
        
        return jsonify({
            'frames': filenames,
            'count': len(filenames)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/download_zip')
def download_zip():
    import zipfile
    
    # Creer le ZIP
    zip_path = os.path.join(OUTPUT_DIR, "car360_images.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(OUTPUT_DIR)):
            if f.endswith('.png') or f.endswith('.jpg'):
                zf.write(os.path.join(OUTPUT_DIR, f), f)
    
    return send_from_directory(OUTPUT_DIR, "car360_images.zip", as_attachment=True)


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Clone Spyne - Video 360")
    print("="*50)
    print("\nUpload une video -> 36 frames -> Sans fond -> Vue 360")
    print(f"Output: {OUTPUT_DIR}")
    print("\nOuvre: http://localhost:5000")
    print("Ctrl+C pour arreter\n")
    app.run(host='0.0.0.0', port=5000, debug=False)

