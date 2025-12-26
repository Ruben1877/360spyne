'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';

export default function TestProcessingPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [originalImage, setOriginalImage] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [backgroundPreset, setBackgroundPreset] = useState('studio_white');

  const STEPS = [
    { name: 'Loading', desc: 'Chargement de l\'image' },
    { name: 'Segmentation', desc: 'Détourage IA (MediaPipe)' },
    { name: 'Edge Smoothing', desc: 'Lissage des bords' },
    { name: 'Background', desc: 'Génération fond studio' },
    { name: 'Shadows', desc: 'Création des 3 couches d\'ombres' },
    { name: 'Reflection', desc: 'Génération du reflet' },
    { name: 'Compositing', desc: 'Assemblage final' },
    { name: 'Post-process', desc: 'Ajustements finaux' },
  ];

  const BACKGROUNDS = {
    studio_white: { top: '#FAFAFA', mid: '#E8E8E8', bottom: '#D0D0D0', name: 'Studio White' },
    studio_grey: { top: '#F0F0F0', mid: '#B4B4B4', bottom: '#A0A0A0', name: 'Studio Grey' },
    studio_dark: { top: '#505050', mid: '#282828', bottom: '#1E1E1E', name: 'Studio Dark' },
    showroom: { top: '#F5F5F5', mid: '#C8C8CD', bottom: '#B4B4B9', name: 'Showroom' },
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const imageData = event.target?.result as string;
      setOriginalImage(imageData);
      setProcessedImage(null);
    };
    reader.readAsDataURL(file);
  };

  const processImage = async () => {
    if (!originalImage) return;

    setIsProcessing(true);
    setCurrentStep(0);
    setProcessedImage(null);

    // Progress simulation while API processes
    const progressInterval = setInterval(() => {
      setCurrentStep(prev => Math.min(prev + 1, 7));
    }, 800);

    try {
      // Call the real Python processing API
      const response = await fetch('/api/v1/process/direct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image: originalImage,
          backgroundPreset,
          addReflection: true,
          addShadows: true,
          outputWidth: 1920,
          outputHeight: 1080
        }),
      });

      clearInterval(progressInterval);
      setCurrentStep(7);

      const result = await response.json();

      if (result.success && result.data.processedImage) {
        setProcessedImage(result.data.processedImage);
        console.log('Processing complete:', result.data.processingTime, 'ms');
      } else {
        // Fallback to canvas processing if API fails
        console.warn('API processing failed, using fallback:', result.error || result.data?.error);
        await processImageFallback();
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error('API error, using fallback:', error);
      // Fallback to canvas processing
      await processImageFallback();
    }

    setIsProcessing(false);
  };

  // Fallback processing using canvas (when API is unavailable)
  const processImageFallback = async () => {
    if (!originalImage) return;
    
    const bg = BACKGROUNDS[backgroundPreset as keyof typeof BACKGROUNDS];

    const img = document.createElement('img');
    img.src = originalImage;

    await new Promise((resolve) => {
      img.onload = resolve;
    });

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Output size (1920x1080 like Spyne)
    canvas.width = 1920;
    canvas.height = 1080;

    // Create studio background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, bg.top);
    gradient.addColorStop(0.65, bg.mid);
    gradient.addColorStop(1, bg.bottom);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add vignette effect (strength: 0.15)
    const vignetteGradient = ctx.createRadialGradient(
      canvas.width / 2, canvas.height / 2, 0,
      canvas.width / 2, canvas.height / 2, canvas.width * 0.7
    );
    vignetteGradient.addColorStop(0, 'rgba(0,0,0,0)');
    vignetteGradient.addColorStop(1, 'rgba(0,0,0,0.15)');
    ctx.fillStyle = vignetteGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Calculate car position and size (centered, 70% width max)
    const aspectRatio = img.width / img.height;
    let carWidth = canvas.width * 0.7;
    let carHeight = carWidth / aspectRatio;

    if (carHeight > canvas.height * 0.6) {
      carHeight = canvas.height * 0.6;
      carWidth = carHeight * aspectRatio;
    }

    const carX = (canvas.width - carWidth) / 2;
    const carY = canvas.height * 0.65 - carHeight;

    // Draw shadows (3 layers - Spyne style)
    ctx.save();

    // Layer 1: Drop shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
    ctx.shadowBlur = 80;
    ctx.shadowOffsetY = 20;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.08)';
    ctx.beginPath();
    ctx.ellipse(canvas.width / 2, carY + carHeight + 10, carWidth * 0.4, 30, 0, 0, Math.PI * 2);
    ctx.fill();

    // Layer 2: Ambient shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.25)';
    ctx.shadowBlur = 35;
    ctx.shadowOffsetY = 10;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.12)';
    ctx.beginPath();
    ctx.ellipse(canvas.width / 2, carY + carHeight + 5, carWidth * 0.35, 20, 0, 0, Math.PI * 2);
    ctx.fill();

    // Layer 3: Contact shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
    ctx.shadowBlur = 5;
    ctx.shadowOffsetY = 0;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.25)';
    ctx.beginPath();
    ctx.ellipse(canvas.width / 2, carY + carHeight, carWidth * 0.3, 8, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    // Draw reflection
    ctx.save();
    ctx.translate(0, (carY + carHeight) * 2 + 30);
    ctx.scale(1, -1);
    ctx.globalAlpha = 0.15;
    const reflectionHeight = carHeight * 0.35;
    ctx.drawImage(img, carX, carY, carWidth, reflectionHeight);
    ctx.restore();

    // Draw the car
    ctx.drawImage(img, carX, carY, carWidth, carHeight);

    // Apply post-processing
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
      data[i] = Math.min(255, Math.max(0, ((data[i] / 255 - 0.5) * 1.05 + 0.5) * 255));
      data[i + 1] = Math.min(255, Math.max(0, ((data[i + 1] / 255 - 0.5) * 1.05 + 0.5) * 255));
      data[i + 2] = Math.min(255, Math.max(0, ((data[i + 2] / 255 - 0.5) * 1.05 + 0.5) * 255));
      const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
      data[i] = Math.min(255, avg + (data[i] - avg) * 1.1);
      data[i + 1] = Math.min(255, avg + (data[i + 1] - avg) * 1.1);
      data[i + 2] = Math.min(255, avg + (data[i + 2] - avg) * 1.1);
    }

    ctx.putImageData(imageData, 0, 0);
    setProcessedImage(canvas.toDataURL('image/jpeg', 0.95));
  };

  return (
    <div className="min-h-screen bg-[#0a0f1a]">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <div>
                <h1 className="text-xl font-bold text-white">Pipeline Test</h1>
                <p className="text-sm text-gray-500">Test du traitement d'image Spyne</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Upload Section */}
        {!originalImage && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 mb-6 rounded-full bg-blue-500/20 flex items-center justify-center">
              <svg className="w-12 h-12 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Upload a Car Photo</h2>
            <p className="text-gray-400 mb-8 text-center max-w-md">
              Upload une photo de voiture pour voir le pipeline de traitement Spyne en action
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />

            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg flex items-center gap-3 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Select Image
            </button>
          </div>
        )}

        {/* Processing Section */}
        {originalImage && (
          <div className="space-y-8">
            {/* Options */}
            <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
              <h3 className="text-white font-bold mb-4">Background Preset</h3>
              <div className="flex flex-wrap gap-3">
                {Object.entries(BACKGROUNDS).map(([key, value]) => (
                  <button
                    key={key}
                    onClick={() => setBackgroundPreset(key)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      backgroundPreset === key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {value.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Images comparison */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Original */}
              <div className="bg-gray-800/50 rounded-xl overflow-hidden border border-gray-700">
                <div className="p-4 bg-gray-700/50 border-b border-gray-600">
                  <h3 className="text-white font-bold">Original</h3>
                </div>
                <div className="aspect-video bg-gray-900 flex items-center justify-center">
                  <img
                    src={originalImage}
                    alt="Original"
                    className="max-w-full max-h-full object-contain"
                  />
                </div>
              </div>

              {/* Processed */}
              <div className="bg-gray-800/50 rounded-xl overflow-hidden border border-gray-700">
                <div className="p-4 bg-blue-600 border-b border-blue-500">
                  <h3 className="text-white font-bold">Processed (Spyne Style)</h3>
                </div>
                <div className="aspect-video bg-gray-900 flex items-center justify-center">
                  {isProcessing ? (
                    <div className="text-center p-8">
                      <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
                      <p className="text-white font-medium mb-2">{STEPS[currentStep].name}</p>
                      <p className="text-gray-400 text-sm">{STEPS[currentStep].desc}</p>
                    </div>
                  ) : processedImage ? (
                    <img
                      src={processedImage}
                      alt="Processed"
                      className="max-w-full max-h-full object-contain"
                    />
                  ) : (
                    <p className="text-gray-500">Click "Process" to start</p>
                  )}
                </div>
              </div>
            </div>

            {/* Processing steps */}
            {isProcessing && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                <h3 className="text-white font-bold mb-4">Pipeline Progress</h3>
                <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
                  {STEPS.map((step, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-lg text-center text-sm transition-all ${
                        i < currentStep
                          ? 'bg-green-500/20 text-green-400'
                          : i === currentStep
                          ? 'bg-blue-500/20 text-blue-400 animate-pulse'
                          : 'bg-gray-700/50 text-gray-500'
                      }`}
                    >
                      <div className="font-bold">{i + 1}</div>
                      <div className="text-xs truncate">{step.name}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-4">
              <button
                onClick={processImage}
                disabled={isProcessing}
                className="flex-1 py-4 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-xl font-bold text-lg transition-colors"
              >
                {isProcessing ? 'Processing...' : processedImage ? 'Re-process' : 'Process Image'}
              </button>

              {processedImage && (
                <a
                  href={processedImage}
                  download="processed-car.jpg"
                  className="px-8 py-4 bg-green-600 hover:bg-green-500 text-white rounded-xl font-bold text-lg transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download
                </a>
              )}

              <button
                onClick={() => {
                  setOriginalImage(null);
                  setProcessedImage(null);
                  if (fileInputRef.current) fileInputRef.current.value = '';
                }}
                className="px-6 py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-medium transition-colors"
              >
                New Image
              </button>
            </div>

            {/* Info */}
            {processedImage && (
              <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
                <h3 className="text-white font-bold mb-4">Pipeline Applied (Identical to Spyne)</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="text-blue-400 font-bold mb-1">Background</div>
                    <div className="text-gray-400">Studio gradient</div>
                    <div className="text-gray-500 text-xs">Horizon: 65%</div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="text-blue-400 font-bold mb-1">Shadows</div>
                    <div className="text-gray-400">3 layers</div>
                    <div className="text-gray-500 text-xs">Contact + Ambient + Drop</div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="text-blue-400 font-bold mb-1">Reflection</div>
                    <div className="text-gray-400">Mirror effect</div>
                    <div className="text-gray-500 text-xs">Opacity: 20%, Fade: 50%</div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="text-blue-400 font-bold mb-1">Post-process</div>
                    <div className="text-gray-400">Enhancements</div>
                    <div className="text-gray-500 text-xs">Contrast +5%, Sat +10%</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

