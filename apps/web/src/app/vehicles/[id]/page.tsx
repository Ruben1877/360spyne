'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  Car, 
  ArrowLeft, 
  Download, 
  Share2, 
  Camera,
  RotateCcw,
  CheckCircle2,
  Clock,
  Palette,
  Settings2,
  Play
} from 'lucide-react';
import Viewer360 from '@/components/Viewer360';

// Demo data
const DEMO_VEHICLE = {
  id: '1',
  make: 'BMW',
  model: 'M4 Competition',
  year: 2024,
  type: 'coupe',
  color: 'Alpine White',
  vin: 'WBS43AZ01NCJ12345',
  status: 'completed' as const,
  images: Array(8).fill(null).map((_, i) => ({
    id: `1-${i}`,
    angleIndex: i,
    angleName: ['Front', 'Front Right', 'Right', 'Rear Right', 'Rear', 'Rear Left', 'Left', 'Front Left'][i],
    inputUrl: `https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800`,
    processedUrl: `https://images.unsplash.com/photo-1555215695-3004980ad54e?w=1920&h=1080&fit=crop&q=90`,
    status: 'completed'
  })),
  createdAt: new Date().toISOString(),
  processedAt: new Date().toISOString()
};

export default function VehicleDetailPage() {
  const params = useParams();
  const [vehicle, setVehicle] = useState(DEMO_VEHICLE);
  const [selectedBackground, setSelectedBackground] = useState('studio_white');
  const [isProcessing, setIsProcessing] = useState(false);

  const backgroundOptions = [
    { id: 'studio_white', name: 'Studio White', color: '#f8f8f8' },
    { id: 'studio_grey', name: 'Studio Grey', color: '#d0d0d0' },
    { id: 'studio_dark', name: 'Studio Dark', color: '#2a2a2a' },
    { id: 'showroom', name: 'Showroom', color: '#e8e8ea' },
    { id: 'outdoor', name: 'Outdoor', color: '#c8d4e0' }
  ];

  const processedImages = vehicle.images
    .filter(img => img.status === 'completed' && img.processedUrl)
    .sort((a, b) => a.angleIndex - b.angleIndex)
    .map(img => img.processedUrl!);

  return (
    <div className="min-h-screen bg-[#0a0f1a]">
      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/vehicles"
                className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-white">
                  {vehicle.year} {vehicle.make} {vehicle.model}
                </h1>
                <p className="text-sm text-gray-500 capitalize">{vehicle.type}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white transition-colors">
                <Share2 className="w-4 h-4" />
                Share
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-spyne-600 hover:bg-spyne-500 text-white font-medium transition-colors">
                <Download className="w-4 h-4" />
                Export All
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left: 360 Viewer */}
          <div className="lg:col-span-2 space-y-6">
            {/* Main viewer */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="aspect-[16/10] rounded-2xl overflow-hidden"
            >
              <Viewer360
                images={processedImages}
                vehicleName={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
                autoPlay={false}
                className="w-full h-full"
              />
            </motion.div>

            {/* Thumbnail strip */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {vehicle.images.map((img, i) => (
                <motion.div
                  key={img.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex-shrink-0"
                >
                  <div className="w-20 h-14 rounded-lg overflow-hidden bg-gray-800 border-2 border-transparent hover:border-spyne-500 transition-colors cursor-pointer">
                    {img.processedUrl ? (
                      <img
                        src={img.processedUrl}
                        alt={img.angleName}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Camera className="w-4 h-4 text-gray-600" />
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 text-center mt-1">{img.angleName}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Right: Details & Controls */}
          <div className="space-y-6">
            {/* Status card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800"
            >
              <div className="flex items-center gap-3 mb-4">
                {vehicle.status === 'completed' ? (
                  <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                  </div>
                ) : (
                  <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <RotateCcw className="w-5 h-5 text-blue-400 animate-spin" />
                  </div>
                )}
                <div>
                  <h3 className="font-semibold text-white">
                    {vehicle.status === 'completed' ? 'Ready' : 'Processing'}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {vehicle.images.filter(i => i.status === 'completed').length} / {vehicle.images.length} images
                  </p>
                </div>
              </div>

              {/* Progress */}
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 1 }}
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full"
                />
              </div>
            </motion.div>

            {/* Vehicle details */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800"
            >
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Car className="w-5 h-5 text-spyne-400" />
                Vehicle Details
              </h3>
              
              <div className="space-y-3">
                {[
                  { label: 'Make', value: vehicle.make },
                  { label: 'Model', value: vehicle.model },
                  { label: 'Year', value: vehicle.year },
                  { label: 'Type', value: vehicle.type, capitalize: true },
                  { label: 'Color', value: vehicle.color || 'N/A' },
                  { label: 'VIN', value: vehicle.vin || 'N/A' }
                ].map((item) => (
                  <div key={item.label} className="flex justify-between">
                    <span className="text-gray-500">{item.label}</span>
                    <span className={`text-white ${item.capitalize ? 'capitalize' : ''}`}>
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Background selector */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800"
            >
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Palette className="w-5 h-5 text-spyne-400" />
                Background Style
              </h3>
              
              <div className="grid grid-cols-5 gap-2">
                {backgroundOptions.map((bg) => (
                  <button
                    key={bg.id}
                    onClick={() => setSelectedBackground(bg.id)}
                    className={`aspect-square rounded-lg border-2 transition-all ${
                      selectedBackground === bg.id
                        ? 'border-spyne-500 ring-2 ring-spyne-500/30'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                    style={{ backgroundColor: bg.color }}
                    title={bg.name}
                  />
                ))}
              </div>
              
              <button
                onClick={() => setIsProcessing(true)}
                disabled={isProcessing}
                className="w-full mt-4 py-2.5 rounded-lg bg-spyne-600 hover:bg-spyne-500 disabled:bg-gray-700 text-white font-medium transition-colors flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" />
                    Reprocessing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Apply & Reprocess
                  </>
                )}
              </button>
            </motion.div>

            {/* Quick actions */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800"
            >
              <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-spyne-400" />
                Export Options
              </h3>
              
              <div className="space-y-2">
                <button className="w-full py-2.5 rounded-lg border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white transition-colors flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  Download ZIP (8 images)
                </button>
                <button className="w-full py-2.5 rounded-lg border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white transition-colors flex items-center justify-center gap-2">
                  <RotateCcw className="w-4 h-4" />
                  Export 360° Embed
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}

