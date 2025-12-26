'use client';

import React, { useRef, useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, Play, Pause, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface Viewer360Props {
  images: string[];
  vehicleName?: string;
  autoPlay?: boolean;
  autoPlaySpeed?: number;
  showControls?: boolean;
  className?: string;
}

export default function Viewer360({
  images,
  vehicleName = 'Vehicle',
  autoPlay = false,
  autoPlaySpeed = 150,
  showControls = true,
  className = ''
}: Viewer360Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadedCount, setLoadedCount] = useState(0);

  // Preload all images
  useEffect(() => {
    setIsLoading(true);
    setLoadedCount(0);
    
    let loaded = 0;
    images.forEach((src) => {
      const img = new window.Image();
      img.onload = () => {
        loaded++;
        setLoadedCount(loaded);
        if (loaded === images.length) {
          setIsLoading(false);
        }
      };
      img.onerror = () => {
        loaded++;
        setLoadedCount(loaded);
        if (loaded === images.length) {
          setIsLoading(false);
        }
      };
      img.src = src;
    });
  }, [images]);

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying || isDragging || images.length === 0) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % images.length);
    }, autoPlaySpeed);

    return () => clearInterval(interval);
  }, [isPlaying, isDragging, images.length, autoPlaySpeed]);

  // Mouse/Touch handlers
  const handleStart = useCallback((clientX: number) => {
    setIsDragging(true);
    setStartX(clientX);
    setIsPlaying(false);
  }, []);

  const handleMove = useCallback((clientX: number) => {
    if (!isDragging) return;

    const diff = clientX - startX;
    const threshold = 20;

    if (Math.abs(diff) > threshold) {
      if (diff > 0) {
        setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
      } else {
        setCurrentIndex((prev) => (prev + 1) % images.length);
      }
      setStartX(clientX);
    }
  }, [isDragging, startX, images.length]);

  const handleEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Mouse events
  const handleMouseDown = (e: React.MouseEvent) => handleStart(e.clientX);
  const handleMouseMove = (e: React.MouseEvent) => handleMove(e.clientX);
  const handleMouseUp = () => handleEnd();
  const handleMouseLeave = () => handleEnd();

  // Touch events
  const handleTouchStart = (e: React.TouchEvent) => handleStart(e.touches[0].clientX);
  const handleTouchMove = (e: React.TouchEvent) => handleMove(e.touches[0].clientX);
  const handleTouchEnd = () => handleEnd();

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Zoom controls
  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 1));

  if (images.length === 0) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 rounded-2xl ${className}`}>
        <div className="text-center text-gray-500 p-12">
          <RotateCcw className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No images available</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-b from-gray-800 to-gray-900 ${className}`}
    >
      {/* Loading overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-20 flex items-center justify-center bg-gray-900"
          >
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-spyne-500/20 border-t-spyne-500 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-400">
                Loading... {loadedCount}/{images.length}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main viewer */}
      <div
        className="viewer-360 relative w-full h-full"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        {/* Image */}
        <div 
          className="w-full h-full flex items-center justify-center transition-transform duration-100"
          style={{ transform: `scale(${zoom})` }}
        >
          <Image
            src={images[currentIndex]}
            alt={`${vehicleName} - View ${currentIndex + 1}`}
            fill
            className="object-contain"
            draggable={false}
            priority={currentIndex === 0}
          />
        </div>

        {/* Drag instruction overlay (show briefly) */}
        {!isDragging && currentIndex === 0 && !isPlaying && (
          <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: 0 }}
            transition={{ delay: 3 }}
            className="absolute inset-0 flex items-center justify-center pointer-events-none"
          >
            <div className="bg-black/60 backdrop-blur-sm px-6 py-3 rounded-full text-white flex items-center gap-3">
              <RotateCcw className="w-5 h-5" />
              <span>Drag to rotate</span>
            </div>
          </motion.div>
        )}
      </div>

      {/* Controls */}
      {showControls && (
        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
          <div className="flex items-center justify-between gap-4">
            {/* Left: Position indicator */}
            <div className="flex items-center gap-3">
              <div className="flex gap-1">
                {images.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setCurrentIndex(i)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      i === currentIndex 
                        ? 'bg-spyne-500 w-4' 
                        : 'bg-white/30 hover:bg-white/50'
                    }`}
                  />
                ))}
              </div>
              <span className="text-white/60 text-sm">
                {currentIndex + 1} / {images.length}
              </span>
            </div>

            {/* Center: Play/Pause */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
              >
                {isPlaying ? (
                  <Pause className="w-5 h-5" />
                ) : (
                  <Play className="w-5 h-5" />
                )}
              </button>
            </div>

            {/* Right: Zoom & Fullscreen */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleZoomOut}
                disabled={zoom <= 1}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors disabled:opacity-30"
              >
                <ZoomOut className="w-5 h-5" />
              </button>
              <span className="text-white/60 text-sm w-12 text-center">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                disabled={zoom >= 3}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors disabled:opacity-30"
              >
                <ZoomIn className="w-5 h-5" />
              </button>
              <button
                onClick={toggleFullscreen}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors ml-2"
              >
                <Maximize2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Vehicle name badge */}
      <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-white text-sm font-medium">
        {vehicleName}
      </div>

      {/* Rotation indicator */}
      {isDragging && (
        <div className="absolute top-4 right-4">
          <RotateCcw className="w-6 h-6 text-spyne-400 animate-spin" />
        </div>
      )}
    </div>
  );
}

