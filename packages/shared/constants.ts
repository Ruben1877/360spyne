/**
 * Shared Constants - Clone Spyne
 * ==============================
 * Constants used across all applications.
 */

// Spyne's S3 URLs (discovered via forensic analysis)
export const SPYNE_S3_URLS = {
  // Car silhouettes
  silhouettes: {
    base: 'https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars',
    hatchback: (index: number) => 
      `https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/${index}.png`,
  },
  
  // Exterior overlays
  exteriorOverlays: {
    front: 'https://spyne-static.s3.amazonaws.com/overlays/Front.png',
    rightFront: 'https://spyne-static.s3.amazonaws.com/overlays/Right+Front.png',
    rightRear: 'https://spyne-static.s3.amazonaws.com/overlays/Right+Rear.png',
    leftFront: 'https://spyne-static.s3.amazonaws.com/overlays/Left+Front.png',
    leftRear: 'https://spyne-static.s3.amazonaws.com/overlays/Left+Rear.png',
    rear: 'https://spyne-static.s3.amazonaws.com/overlays/Rear.png',
  },
  
  // Interior overlays
  interiorOverlays: {
    dashboard: 'https://spyne-test.s3.amazonaws.com/interiorOverlays/Dashboard.png',
    centerDash: 'https://spyne-test.s3.amazonaws.com/interiorOverlays/Center+dash.png',
  },
};

// Background presets with their exact colors
export const BACKGROUND_PRESETS = {
  studio_white: {
    name: 'Studio White',
    topColor: [250, 250, 250],
    horizonColor: [240, 240, 240],
    floorColor: [215, 215, 215],
    horizonPosition: 0.65,
  },
  studio_grey: {
    name: 'Studio Grey',
    topColor: [235, 235, 235],
    horizonColor: [210, 210, 210],
    floorColor: [175, 175, 175],
    horizonPosition: 0.65,
  },
  studio_dark: {
    name: 'Studio Dark',
    topColor: [90, 90, 90],
    horizonColor: [60, 60, 60],
    floorColor: [35, 35, 35],
    horizonPosition: 0.65,
  },
  showroom: {
    name: 'Showroom',
    topColor: [248, 248, 250],
    horizonColor: [230, 230, 235],
    floorColor: [195, 195, 200],
    horizonPosition: 0.60,
  },
  dealership: {
    name: 'Dealership Floor',
    topColor: [245, 245, 247],
    horizonColor: [225, 225, 230],
    floorColor: [185, 185, 195],
    horizonPosition: 0.62,
  },
  outdoor_neutral: {
    name: 'Outdoor Neutral',
    topColor: [200, 210, 220],
    horizonColor: [180, 185, 190],
    floorColor: [160, 165, 170],
    horizonPosition: 0.55,
  },
} as const;

// Shadow configurations (reverse-engineered from Spyne)
export const SHADOW_CONFIG = {
  contact: {
    blurRadius: 5,
    opacity: 0.45,
    offsetY: 0,
    scaleY: 0.015,
  },
  ambient: {
    blurRadius: 35,
    opacity: 0.25,
    offsetY: 5,
    scaleY: 0.12,
  },
  drop: {
    blurRadius: 80,
    opacity: 0.15,
    offsetY: 15,
    scaleY: 0.20,
  },
};

// Post-processing defaults
export const POST_PROCESSING_DEFAULTS = {
  brightness: 1.0,
  contrast: 1.05,
  saturation: 1.10,
  sharpness: 1.10,
};

// Output sizes
export const OUTPUT_SIZES = {
  hd: { name: 'HD', width: 1280, height: 720 },
  fullHd: { name: 'Full HD', width: 1920, height: 1080 },
  '2k': { name: '2K', width: 2560, height: 1440 },
  '4k': { name: '4K', width: 3840, height: 2160 },
};

// Supported vehicle types
export const VEHICLE_TYPES = [
  'sedan',
  'suv', 
  'hatchback',
  'truck',
  'coupe',
  'van',
  'other',
] as const;

// Capture configurations
export const CAPTURE_CONFIGS = {
  standard: {
    name: 'Standard (8 angles)',
    angles: 8,
    startAngle: 0,
    stepAngle: 45,
  },
  detailed: {
    name: 'Detailed (12 angles)',
    angles: 12,
    startAngle: 0,
    stepAngle: 30,
  },
  premium: {
    name: 'Premium (36 angles)',
    angles: 36,
    startAngle: 0,
    stepAngle: 10,
  },
};

// API endpoints
export const API_ENDPOINTS = {
  vehicles: '/api/v1/vehicles',
  images: '/api/v1/images',
  process: '/api/v1/process',
  overlays: '/api/v1/overlays',
};

