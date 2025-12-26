'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import Image from 'next/image';

// Capture angles configuration (same as Spyne)
const ANGLES = [
  { id: 0, name: 'Front', angle: 0, instruction: 'Stand directly in front of the vehicle' },
  { id: 1, name: 'Front Right', angle: 45, instruction: 'Move 45° to the right' },
  { id: 2, name: 'Right Side', angle: 90, instruction: 'Stand at the right side' },
  { id: 3, name: 'Rear Right', angle: 135, instruction: 'Move 45° toward the rear' },
  { id: 4, name: 'Rear', angle: 180, instruction: 'Stand directly behind' },
  { id: 5, name: 'Rear Left', angle: 225, instruction: 'Move 45° to the left' },
  { id: 6, name: 'Left Side', angle: 270, instruction: 'Stand at the left side' },
  { id: 7, name: 'Front Left', angle: 315, instruction: 'Move 45° toward the front' },
];

// Spyne silhouettes from their S3
const SILHOUETTES = [
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/1.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/5.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/10.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/14.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/19.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/23.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/28.png',
  'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/32.png',
];

export default function MobileCapturePage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [currentAngle, setCurrentAngle] = useState(0);
  const [photos, setPhotos] = useState<string[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOverlay, setShowOverlay] = useState(true);
  const [isComplete, setIsComplete] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [useUploadMode, setUseUploadMode] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [showProcessingDemo, setShowProcessingDemo] = useState(false);

  const angle = ANGLES[currentAngle];
  const progress = (currentAngle / ANGLES.length) * 100;

  // Initialize camera
  useEffect(() => {
    async function initCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'environment',
            width: { ideal: 1920 },
            height: { ideal: 1080 }
          },
          audio: false
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          setStream(mediaStream);
          setCameraReady(true);
        }
      } catch (err) {
        console.error('Camera error:', err);
        setError('Unable to access camera. Please allow camera permissions.');
      }
    }
    
    initCamera();
    
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Capture photo
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || isCapturing) return;
    
    setIsCapturing(true);
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    // Set canvas size to video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);
    
    // Get image data
    const imageData = canvas.toDataURL('image/jpeg', 0.9);
    
    // Add to photos
    const newPhotos = [...photos, imageData];
    setPhotos(newPhotos);
    
    // Flash effect
    const flash = document.getElementById('flash');
    if (flash) {
      flash.style.opacity = '1';
      setTimeout(() => {
        flash.style.opacity = '0';
      }, 100);
    }
    
    // Move to next angle or complete
    setTimeout(() => {
      if (currentAngle < ANGLES.length - 1) {
        setCurrentAngle(currentAngle + 1);
      } else {
        setIsComplete(true);
      }
      setIsCapturing(false);
    }, 300);
  }, [currentAngle, photos, isCapturing]);

  // Skip to next angle
  const skipAngle = () => {
    if (currentAngle < ANGLES.length - 1) {
      setCurrentAngle(currentAngle + 1);
    }
  };

  // Go back to previous
  const previousAngle = () => {
    if (currentAngle > 0) {
      setCurrentAngle(currentAngle - 1);
      setPhotos(photos.slice(0, -1));
    }
  };

  // Upload photos (simulate for now)
  const handleUpload = async () => {
    alert(`✅ ${photos.length} photos captured!\n\nSession: ${sessionId}\n\nIn production, these would be uploaded to the server for processing.`);
  };

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const imageData = event.target?.result as string;
      setPhotos([...photos, imageData]);
      
      if (currentAngle < ANGLES.length - 1) {
        setCurrentAngle(currentAngle + 1);
      } else {
        setIsComplete(true);
      }
    };
    reader.readAsDataURL(file);
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Simulate processing pipeline
  const processImage = async (imageData: string) => {
    setIsProcessing(true);
    setShowProcessingDemo(true);
    
    // Simulate the 8-step pipeline
    await new Promise(r => setTimeout(r, 500));
    
    // For demo, we'll create a processed version using canvas
    const img = document.createElement('img');
    img.src = imageData;
    
    await new Promise((resolve) => {
      img.onload = resolve;
    });
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Output size like Spyne
    canvas.width = 1920;
    canvas.height = 1080;
    
    // Create studio background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#FAFAFA');
    gradient.addColorStop(0.65, '#E8E8E8');
    gradient.addColorStop(1, '#D0D0D0');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Add vignette effect
    const vignetteGradient = ctx.createRadialGradient(
      canvas.width / 2, canvas.height / 2, 0,
      canvas.width / 2, canvas.height / 2, canvas.width * 0.7
    );
    vignetteGradient.addColorStop(0, 'rgba(0,0,0,0)');
    vignetteGradient.addColorStop(1, 'rgba(0,0,0,0.15)');
    ctx.fillStyle = vignetteGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Calculate car position and size
    const aspectRatio = img.width / img.height;
    let carWidth = canvas.width * 0.7;
    let carHeight = carWidth / aspectRatio;
    
    if (carHeight > canvas.height * 0.6) {
      carHeight = canvas.height * 0.6;
      carWidth = carHeight * aspectRatio;
    }
    
    const carX = (canvas.width - carWidth) / 2;
    const carY = canvas.height * 0.65 - carHeight;
    
    // Draw shadow layers
    ctx.save();
    
    // Drop shadow (very blurry, large)
    ctx.shadowColor = 'rgba(0, 0, 0, 0.15)';
    ctx.shadowBlur = 80;
    ctx.shadowOffsetY = 20;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.fillRect(carX + 50, carY + carHeight - 20, carWidth - 100, 40);
    
    // Ambient shadow (medium blur)
    ctx.shadowColor = 'rgba(0, 0, 0, 0.25)';
    ctx.shadowBlur = 35;
    ctx.shadowOffsetY = 10;
    ctx.fillRect(carX + 30, carY + carHeight - 15, carWidth - 60, 25);
    
    // Contact shadow (sharp, small)
    ctx.shadowColor = 'rgba(0, 0, 0, 0.45)';
    ctx.shadowBlur = 5;
    ctx.shadowOffsetY = 0;
    ctx.fillRect(carX + 20, carY + carHeight - 5, carWidth - 40, 10);
    
    ctx.restore();
    
    // Draw reflection (flipped car with gradient fade)
    ctx.save();
    ctx.translate(0, carY + carHeight * 2 + 20);
    ctx.scale(1, -1);
    ctx.globalAlpha = 0.15;
    ctx.drawImage(img, carX, carY, carWidth, carHeight * 0.4);
    ctx.restore();
    
    // Draw the car
    ctx.drawImage(img, carX, carY, carWidth, carHeight);
    
    // Apply post-processing (slight contrast/saturation boost)
    const imageDataObj = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageDataObj.data;
    
    for (let i = 0; i < data.length; i += 4) {
      // Contrast boost (1.05)
      data[i] = Math.min(255, ((data[i] / 255 - 0.5) * 1.05 + 0.5) * 255);
      data[i + 1] = Math.min(255, ((data[i + 1] / 255 - 0.5) * 1.05 + 0.5) * 255);
      data[i + 2] = Math.min(255, ((data[i + 2] / 255 - 0.5) * 1.05 + 0.5) * 255);
    }
    
    ctx.putImageData(imageDataObj, 0, 0);
    
    setProcessedImage(canvas.toDataURL('image/jpeg', 0.95));
    setIsProcessing(false);
  };

  // Error state - Show upload mode option
  if (error && !useUploadMode) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Camera Error</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          
          <div className="space-y-3">
            <button
              onClick={() => window.location.reload()}
              className="w-full px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-medium"
            >
              Try Camera Again
            </button>
            
            <button
              onClick={() => setUseUploadMode(true)}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Upload Images Instead
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Processing demo view
  if (showProcessingDemo) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-white mb-6 text-center">
            Image Processing Pipeline
          </h1>
          
          {isProcessing ? (
            <div className="text-center py-20">
              <div className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-6" />
              <h2 className="text-xl font-bold text-white mb-2">Processing Image...</h2>
              <div className="space-y-2 text-gray-400 text-sm">
                <p>1. Segmentation (AI)</p>
                <p>2. Edge Smoothing</p>
                <p>3. Background Generation</p>
                <p>4. Shadow Layers (3x)</p>
                <p>5. Reflection</p>
                <p>6. Compositing</p>
                <p>7. Post-processing</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Before/After comparison */}
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-gray-800 rounded-xl overflow-hidden">
                  <div className="p-3 bg-gray-700">
                    <h3 className="text-white font-medium text-center">Original</h3>
                  </div>
                  <div className="aspect-video bg-gray-900 flex items-center justify-center">
                    {photos[0] && (
                      <img src={photos[0]} alt="Original" className="max-w-full max-h-full object-contain" />
                    )}
                  </div>
                </div>
                
                <div className="bg-gray-800 rounded-xl overflow-hidden">
                  <div className="p-3 bg-blue-600">
                    <h3 className="text-white font-medium text-center">Processed (Spyne Style)</h3>
                  </div>
                  <div className="aspect-video bg-gray-900 flex items-center justify-center">
                    {processedImage && (
                      <img src={processedImage} alt="Processed" className="max-w-full max-h-full object-contain" />
                    )}
                  </div>
                </div>
              </div>
              
              {/* Processing details */}
              <div className="bg-gray-800 rounded-xl p-6">
                <h3 className="text-white font-bold mb-4">Pipeline Applied:</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="bg-gray-700 rounded-lg p-3 text-center">
                    <div className="text-blue-400 font-bold">Background</div>
                    <div className="text-gray-400">Studio gradient</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3 text-center">
                    <div className="text-blue-400 font-bold">Shadows</div>
                    <div className="text-gray-400">3 layers</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3 text-center">
                    <div className="text-blue-400 font-bold">Reflection</div>
                    <div className="text-gray-400">20% opacity</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3 text-center">
                    <div className="text-blue-400 font-bold">Post-process</div>
                    <div className="text-gray-400">Contrast +5%</div>
                  </div>
                </div>
              </div>
              
              {/* Download button */}
              <div className="flex gap-4">
                <a
                  href={processedImage || '#'}
                  download="processed-car.jpg"
                  className="flex-1 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-center"
                >
                  Download Processed Image
                </a>
                <button
                  onClick={() => {
                    setShowProcessingDemo(false);
                    setProcessedImage(null);
                  }}
                  className="px-6 py-4 bg-gray-700 hover:bg-gray-600 text-white rounded-xl font-medium"
                >
                  Back
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Complete state
  if (isComplete) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="max-w-md mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Capture Complete!</h1>
            <p className="text-gray-400">{photos.length} photos captured</p>
          </div>

          {/* Photo grid */}
          <div className="grid grid-cols-4 gap-2 mb-8">
            {photos.map((photo, i) => (
              <div 
                key={i} 
                className="aspect-square rounded-lg overflow-hidden bg-gray-800 cursor-pointer hover:ring-2 hover:ring-blue-500"
                onClick={() => processImage(photo)}
              >
                <img src={photo} alt={`Angle ${i + 1}`} className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
          
          <p className="text-center text-gray-500 text-sm mb-6">
            Click on any photo to see the processing demo
          </p>

          {/* Actions */}
          <div className="space-y-3">
            <button
              onClick={() => processImage(photos[0])}
              className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg"
            >
              Process First Image (Demo)
            </button>
            <button
              onClick={handleUpload}
              className="w-full py-4 bg-green-600 hover:bg-green-500 text-white rounded-xl font-bold text-lg"
            >
              Upload All Photos
            </button>
            <button
              onClick={() => {
                setPhotos([]);
                setCurrentAngle(0);
                setIsComplete(false);
              }}
              className="w-full py-4 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-medium"
            >
              Start Over
            </button>
          </div>

          {/* Session info */}
          <div className="mt-8 p-4 bg-gray-800 rounded-xl text-center">
            <p className="text-xs text-gray-500 mb-1">Session ID</p>
            <p className="font-mono font-bold text-white">{sessionId}</p>
          </div>
        </div>
      </div>
    );
  }

  // Upload mode UI
  if (useUploadMode) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="max-w-md mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => setUseUploadMode(false)}
              className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center"
            >
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div className="text-center">
              <h1 className="text-xl font-bold text-white">Upload Mode</h1>
              <p className="text-sm text-gray-500">{currentAngle + 1} / {ANGLES.length}</p>
            </div>
            <div className="w-10" />
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-gray-800 rounded-full mb-6 overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Current angle info */}
          <div className="bg-gray-800 rounded-xl p-6 mb-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-blue-500/20 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-blue-400">{angle.angle}°</span>
            </div>
            <h2 className="text-xl font-bold text-white mb-2">{angle.name}</h2>
            <p className="text-gray-400">{angle.instruction}</p>
          </div>

          {/* Silhouette preview */}
          <div className="bg-gray-800 rounded-xl p-4 mb-6">
            <p className="text-xs text-gray-500 text-center mb-2">Reference angle</p>
            <img
              src={SILHOUETTES[currentAngle]}
              alt={`${angle.name} reference`}
              className="w-full h-40 object-contain opacity-60"
            />
          </div>

          {/* Upload button */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-lg flex items-center justify-center gap-3"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Upload {angle.name} Photo
          </button>

          {/* Skip button */}
          <button
            onClick={skipAngle}
            className="w-full mt-3 py-3 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-xl font-medium"
          >
            Skip this angle
          </button>

          {/* Photo thumbnails */}
          {photos.length > 0 && (
            <div className="mt-6">
              <p className="text-sm text-gray-500 mb-2">Uploaded photos:</p>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {photos.map((photo, i) => (
                  <div key={i} className="w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden border-2 border-green-500">
                    <img src={photo} alt="" className="w-full h-full object-cover" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black">
      {/* Hidden canvas for capture */}
      <canvas ref={canvasRef} className="hidden" />
      
      {/* Camera view */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Flash effect */}
      <div
        id="flash"
        className="absolute inset-0 bg-white pointer-events-none transition-opacity duration-100"
        style={{ opacity: 0 }}
      />

      {/* Overlay silhouette */}
      {showOverlay && cameraReady && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <img
            src={SILHOUETTES[currentAngle]}
            alt="Guide"
            className="w-4/5 h-auto opacity-40"
            style={{ maxHeight: '50vh' }}
          />
        </div>
      )}

      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/70 to-transparent">
        <div className="flex items-center justify-between">
          {/* Close button */}
          <button
            onClick={() => window.history.back()}
            className="w-10 h-10 rounded-full bg-black/50 flex items-center justify-center"
          >
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Angle indicator */}
          <div className="bg-black/50 px-4 py-2 rounded-full">
            <p className="text-blue-400 font-bold text-lg">{currentAngle + 1} / {ANGLES.length}</p>
            <p className="text-white text-sm text-center">{angle.name}</p>
          </div>

          {/* Toggle overlay */}
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className="w-10 h-10 rounded-full bg-black/50 flex items-center justify-center"
          >
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {showOverlay ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              )}
            </svg>
          </button>
        </div>

        {/* Progress bar */}
        <div className="mt-4 h-1 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Instruction */}
      <div className="absolute bottom-40 left-4 right-4">
        <div className="bg-black/70 rounded-xl px-4 py-3 text-center">
          <p className="text-white text-sm">{angle.instruction}</p>
        </div>
      </div>

      {/* Bottom controls */}
      <div className="absolute bottom-8 left-0 right-0 px-6">
        <div className="flex items-center justify-around">
          {/* Previous */}
          <button
            onClick={previousAngle}
            disabled={currentAngle === 0}
            className={`w-14 h-14 rounded-full flex items-center justify-center ${
              currentAngle === 0 ? 'bg-gray-800 opacity-30' : 'bg-white/20'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Capture button */}
          <button
            onClick={capturePhoto}
            disabled={!cameraReady || isCapturing}
            className="w-20 h-20 rounded-full bg-white border-4 border-blue-500 flex items-center justify-center disabled:opacity-50"
          >
            <div className={`w-16 h-16 rounded-full bg-blue-500 ${isCapturing ? 'animate-pulse' : ''}`} />
          </button>

          {/* Skip */}
          <button
            onClick={skipAngle}
            disabled={currentAngle === ANGLES.length - 1}
            className={`w-14 h-14 rounded-full flex items-center justify-center ${
              currentAngle === ANGLES.length - 1 ? 'bg-gray-800 opacity-30' : 'bg-white/20'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Photo thumbnails */}
        {photos.length > 0 && (
          <div className="mt-4 flex justify-center gap-2">
            {photos.slice(-4).map((photo, i) => (
              <div key={i} className="w-10 h-10 rounded-lg overflow-hidden border-2 border-white">
                <img src={photo} alt="" className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Loading overlay */}
      {!cameraReady && (
        <div className="absolute inset-0 bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white">Initializing camera...</p>
          </div>
        </div>
      )}
    </div>
  );
}

