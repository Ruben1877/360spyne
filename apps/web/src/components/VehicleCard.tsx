'use client';

import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Car, Camera, CheckCircle2, Clock, AlertCircle, RotateCcw } from 'lucide-react';

interface VehicleImage {
  id: string;
  angleIndex: number;
  processedUrl?: string;
  status: string;
}

interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  type: string;
  status: 'pending' | 'capturing' | 'processing' | 'completed';
  images: VehicleImage[];
  createdAt: string;
}

interface VehicleCardProps {
  vehicle: Vehicle;
  index?: number;
}

const statusConfig = {
  pending: {
    icon: Clock,
    label: 'Pending',
    className: 'status-pending'
  },
  capturing: {
    icon: Camera,
    label: 'Capturing',
    className: 'status-processing'
  },
  processing: {
    icon: RotateCcw,
    label: 'Processing',
    className: 'status-processing'
  },
  completed: {
    icon: CheckCircle2,
    label: 'Completed',
    className: 'status-completed'
  }
};

export default function VehicleCard({ vehicle, index = 0 }: VehicleCardProps) {
  const status = statusConfig[vehicle.status];
  const StatusIcon = status.icon;
  
  const completedImages = vehicle.images.filter(img => img.status === 'completed').length;
  const totalImages = vehicle.images.length;
  const progress = totalImages > 0 ? (completedImages / totalImages) * 100 : 0;
  
  const thumbnailUrl = vehicle.images.find(img => img.processedUrl)?.processedUrl;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link href={`/vehicles/${vehicle.id}`}>
        <div className="group relative rounded-2xl overflow-hidden bg-gray-900/50 border border-gray-800 hover:border-spyne-500/50 transition-all card-hover">
          {/* Thumbnail */}
          <div className="relative aspect-[16/10] overflow-hidden bg-gray-800">
            {thumbnailUrl ? (
              <Image
                src={thumbnailUrl}
                alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
                fill
                className="object-cover group-hover:scale-105 transition-transform duration-500"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <Car className="w-16 h-16 text-gray-700" />
              </div>
            )}
            
            {/* Overlay gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-transparent opacity-60" />
            
            {/* Status badge */}
            <div className={`absolute top-3 right-3 px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 border ${status.className}`}>
              <StatusIcon className={`w-3.5 h-3.5 ${vehicle.status === 'processing' ? 'animate-spin' : ''}`} />
              {status.label}
            </div>
            
            {/* 360 indicator */}
            {vehicle.status === 'completed' && (
              <div className="absolute bottom-3 right-3 px-2 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs flex items-center gap-1.5">
                <RotateCcw className="w-3 h-3" />
                360°
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-4">
            {/* Title */}
            <h3 className="font-semibold text-lg text-white group-hover:text-spyne-400 transition-colors">
              {vehicle.year} {vehicle.make} {vehicle.model}
            </h3>
            
            {/* Type */}
            <p className="text-gray-500 text-sm capitalize mt-0.5">
              {vehicle.type}
            </p>

            {/* Progress bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1.5">
                <span>Photos</span>
                <span>{completedImages} / {totalImages}</span>
              </div>
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5, delay: index * 0.05 + 0.2 }}
                  className={`h-full rounded-full ${
                    progress === 100 
                      ? 'bg-gradient-to-r from-green-500 to-emerald-400' 
                      : 'bg-gradient-to-r from-spyne-500 to-spyne-400'
                  }`}
                />
              </div>
            </div>

            {/* Date */}
            <div className="mt-3 pt-3 border-t border-gray-800">
              <p className="text-xs text-gray-600">
                Created {new Date(vehicle.createdAt).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

