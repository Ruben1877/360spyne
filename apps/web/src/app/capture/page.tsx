'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';
import { 
  Car, 
  ArrowLeft, 
  Smartphone, 
  QrCode, 
  CheckCircle2, 
  ArrowRight,
  Copy,
  ExternalLink,
  RefreshCw
} from 'lucide-react';

// Real QR code component
function QRCodeDisplay({ value }: { value: string }) {
  return (
    <div className="relative w-64 h-64 bg-white rounded-2xl p-4 flex items-center justify-center">
      <QRCodeSVG
        value={value}
        size={220}
        level="M"
        includeMargin={false}
        bgColor="#FFFFFF"
        fgColor="#000000"
        imageSettings={{
          src: '/car-icon.svg',
          x: undefined,
          y: undefined,
          height: 30,
          width: 30,
          excavate: true,
        }}
      />
    </div>
  );
}

export default function CapturePage() {
  const [step, setStep] = useState<'create' | 'qr' | 'waiting'>('create');
  const [vehicleData, setVehicleData] = useState({
    make: '',
    model: '',
    year: new Date().getFullYear(),
    type: 'sedan'
  });
  const [captureUrl, setCaptureUrl] = useState('');
  const [sessionId, setSessionId] = useState('');

  const vehicleTypes = [
    { id: 'sedan', name: 'Sedan' },
    { id: 'suv', name: 'SUV' },
    { id: 'hatchback', name: 'Hatchback' },
    { id: 'truck', name: 'Truck' },
    { id: 'coupe', name: 'Coupe' },
    { id: 'van', name: 'Van' }
  ];

  const handleCreateVehicle = async () => {
    // Generate session ID
    const newSessionId = Math.random().toString(36).substring(2, 10).toUpperCase();
    setSessionId(newSessionId);
    
    // Generate capture URL
    const baseUrl = window.location.origin;
    const url = `${baseUrl}/capture/mobile?session=${newSessionId}`;
    setCaptureUrl(url);
    
    setStep('qr');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(captureUrl);
  };

  return (
    <div className="min-h-screen bg-[#0a0f1a] gradient-mesh">
      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Link
              href="/vehicles"
              className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-white">New Capture Session</h1>
              <p className="text-sm text-gray-500">Set up a 360° photo capture</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Steps indicator */}
        <div className="flex items-center justify-center mb-12">
          {['Vehicle Info', 'Scan QR', 'Capture'].map((label, i) => (
            <div key={label} className="flex items-center">
              <div className={`flex items-center gap-2 ${
                i <= (step === 'create' ? 0 : step === 'qr' ? 1 : 2)
                  ? 'text-spyne-400'
                  : 'text-gray-600'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                  i < (step === 'create' ? 0 : step === 'qr' ? 1 : 2)
                    ? 'bg-spyne-500 text-white'
                    : i === (step === 'create' ? 0 : step === 'qr' ? 1 : 2)
                    ? 'bg-spyne-500/20 text-spyne-400 border border-spyne-500'
                    : 'bg-gray-800 text-gray-600'
                }`}>
                  {i < (step === 'create' ? 0 : step === 'qr' ? 1 : 2) ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    i + 1
                  )}
                </div>
                <span className="hidden sm:inline">{label}</span>
              </div>
              {i < 2 && (
                <div className={`w-12 h-0.5 mx-3 ${
                  i < (step === 'create' ? 0 : step === 'qr' ? 1 : 2)
                    ? 'bg-spyne-500'
                    : 'bg-gray-800'
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Create Vehicle */}
        {step === 'create' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-xl mx-auto"
          >
            <div className="p-8 rounded-2xl bg-gray-900/50 border border-gray-800">
              <h2 className="text-2xl font-bold text-white mb-6">Vehicle Information</h2>
              
              <div className="space-y-5">
                {/* Make */}
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Make
                  </label>
                  <input
                    type="text"
                    value={vehicleData.make}
                    onChange={(e) => setVehicleData({ ...vehicleData, make: e.target.value })}
                    placeholder="e.g., BMW, Tesla, Toyota"
                    className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-spyne-500 transition-colors"
                  />
                </div>

                {/* Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Model
                  </label>
                  <input
                    type="text"
                    value={vehicleData.model}
                    onChange={(e) => setVehicleData({ ...vehicleData, model: e.target.value })}
                    placeholder="e.g., M4, Model S, Camry"
                    className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-spyne-500 transition-colors"
                  />
                </div>

                {/* Year */}
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Year
                  </label>
                  <input
                    type="number"
                    value={vehicleData.year}
                    onChange={(e) => setVehicleData({ ...vehicleData, year: parseInt(e.target.value) })}
                    min="1990"
                    max="2030"
                    className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-700 text-white focus:outline-none focus:border-spyne-500 transition-colors"
                  />
                </div>

                {/* Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Vehicle Type
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {vehicleTypes.map((type) => (
                      <button
                        key={type.id}
                        onClick={() => setVehicleData({ ...vehicleData, type: type.id })}
                        className={`px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                          vehicleData.type === type.id
                            ? 'bg-spyne-500/20 border-spyne-500 text-spyne-400'
                            : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                        }`}
                      >
                        {type.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <button
                onClick={handleCreateVehicle}
                disabled={!vehicleData.make || !vehicleData.model}
                className="w-full mt-8 py-3.5 rounded-xl bg-spyne-600 hover:bg-spyne-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold transition-colors flex items-center justify-center gap-2"
              >
                Generate Capture QR
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: QR Code */}
        {step === 'qr' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="inline-block p-8 rounded-2xl bg-gray-900/50 border border-gray-800">
              {/* Vehicle info */}
              <div className="mb-6 pb-6 border-b border-gray-800">
                <h2 className="text-xl font-bold text-white">
                  {vehicleData.year} {vehicleData.make} {vehicleData.model}
                </h2>
                <p className="text-gray-500 capitalize">{vehicleData.type}</p>
              </div>

              {/* QR Code */}
              <div className="flex justify-center mb-6">
                <QRCodeDisplay value={captureUrl} />
              </div>

              {/* Instructions */}
              <div className="mb-6">
                <div className="flex items-center justify-center gap-2 text-spyne-400 mb-2">
                  <Smartphone className="w-5 h-5" />
                  <span className="font-medium">Scan with your phone</span>
                </div>
                <p className="text-sm text-gray-500">
                  Open your camera app and point it at the QR code
                </p>
              </div>

              {/* Session ID */}
              <div className="p-3 rounded-xl bg-gray-800 mb-4">
                <p className="text-xs text-gray-500 mb-1">Session ID</p>
                <p className="text-lg font-mono font-bold text-white tracking-wider">
                  {sessionId}
                </p>
              </div>

              {/* Copy link */}
              <div className="flex gap-2">
                <button
                  onClick={copyToClipboard}
                  className="flex-1 py-2.5 rounded-xl border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white transition-colors flex items-center justify-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  Copy Link
                </button>
                <a
                  href={captureUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 py-2.5 rounded-xl border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white transition-colors flex items-center justify-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  Open Link
                </a>
              </div>
            </div>

            {/* Waiting status */}
            <div className="mt-8 p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 max-w-md mx-auto">
              <div className="flex items-center gap-3">
                <RefreshCw className="w-5 h-5 text-yellow-400 animate-spin" />
                <div className="text-left">
                  <p className="text-yellow-400 font-medium">Waiting for capture</p>
                  <p className="text-yellow-400/70 text-sm">
                    Photos will appear here automatically
                  </p>
                </div>
              </div>
            </div>

            {/* Back button */}
            <button
              onClick={() => setStep('create')}
              className="mt-6 text-gray-500 hover:text-white transition-colors"
            >
              ← Start over
            </button>
          </motion.div>
        )}
      </main>
    </div>
  );
}

