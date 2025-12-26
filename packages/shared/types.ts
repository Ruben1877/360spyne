/**
 * Shared Types - Clone Spyne
 * ==========================
 * Type definitions shared across all apps.
 */

// Vehicle types
export type VehicleType = 'sedan' | 'suv' | 'hatchback' | 'truck' | 'coupe' | 'van' | 'other';
export type VehicleStatus = 'pending' | 'capturing' | 'processing' | 'completed';
export type ImageStatus = 'pending' | 'uploading' | 'uploaded' | 'processing' | 'completed' | 'failed';

export interface Vehicle {
  id: string;
  vin?: string;
  make: string;
  model: string;
  year: number;
  color?: string;
  type: VehicleType;
  status: VehicleStatus;
  images: VehicleImage[];
  createdAt: string;
  updatedAt: string;
}

export interface VehicleImage {
  id: string;
  vehicleId: string;
  angleIndex: number;
  angleName: string;
  inputUrl?: string;
  processedUrl?: string;
  thumbnailUrl?: string;
  status: ImageStatus;
  metadata?: ImageMetadata;
  createdAt: string;
  processedAt?: string;
}

export interface ImageMetadata {
  width: number;
  height: number;
  size: number;
  format: string;
  exif?: Record<string, any>;
}

// Capture angles
export interface CaptureAngle {
  id: number;
  name: string;
  angle: number;
  overlayUrl?: string;
  silhouetteUrl?: string;
  instruction?: string;
}

export const EXTERIOR_ANGLES: CaptureAngle[] = [
  { id: 0, name: 'Front', angle: 0 },
  { id: 1, name: 'Front Right', angle: 45 },
  { id: 2, name: 'Right', angle: 90 },
  { id: 3, name: 'Rear Right', angle: 135 },
  { id: 4, name: 'Rear', angle: 180 },
  { id: 5, name: 'Rear Left', angle: 225 },
  { id: 6, name: 'Left', angle: 270 },
  { id: 7, name: 'Front Left', angle: 315 },
];

// Processing options
export interface ProcessingOptions {
  backgroundPreset: BackgroundPreset;
  addReflection: boolean;
  addShadows: boolean;
  outputSize: [number, number];
  quality: number;
}

export type BackgroundPreset = 
  | 'studio_white'
  | 'studio_grey'
  | 'studio_dark'
  | 'showroom'
  | 'dealership'
  | 'outdoor_neutral';

export interface ProcessingResult {
  success: boolean;
  inputUrl: string;
  outputUrl?: string;
  processingTime?: number;
  error?: string;
}

// API responses
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

// Job types
export interface ProcessingJob {
  id: string;
  vehicleId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  createdAt: string;
  completedAt?: string;
  result?: ProcessingResult[];
  error?: string;
}

