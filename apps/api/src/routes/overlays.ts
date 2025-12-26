/**
 * Overlays Router
 * ===============
 * Serve silhouettes and overlay guides for camera capture.
 * Replicates Spyne's overlay system.
 */

import { Router, Request, Response } from 'express';
import { query, validationResult } from 'express-validator';
import path from 'path';
import fs from 'fs/promises';
import { logger } from '../services/logger.service';

const router = Router();

// Asset paths
const ASSETS_PATH = path.join(__dirname, '../../../assets');

// Overlay configurations (like Spyne)
const VEHICLE_TYPES = ['hatchback', 'sedan', 'suv', 'truck', 'coupe', 'van'];

const EXTERIOR_ANGLES = [
  { id: 0, name: 'Front', angle: 0, overlay: 'front.png' },
  { id: 1, name: 'Front Right', angle: 45, overlay: 'front_right.png' },
  { id: 2, name: 'Right', angle: 90, overlay: 'right.png' },
  { id: 3, name: 'Rear Right', angle: 135, overlay: 'rear_right.png' },
  { id: 4, name: 'Rear', angle: 180, overlay: 'rear.png' },
  { id: 5, name: 'Rear Left', angle: 225, overlay: 'rear_left.png' },
  { id: 6, name: 'Left', angle: 270, overlay: 'left.png' },
  { id: 7, name: 'Front Left', angle: 315, overlay: 'front_left.png' }
];

const INTERIOR_OVERLAYS = [
  { id: 'dashboard', name: 'Dashboard', overlay: 'dashboard.png' },
  { id: 'center_dash', name: 'Center Dash', overlay: 'center_dash.png' },
  { id: 'steering', name: 'Steering Wheel', overlay: 'steering.png' },
  { id: 'front_seats', name: 'Front Seats', overlay: 'front_seats.png' },
  { id: 'rear_seats', name: 'Rear Seats', overlay: 'rear_seats.png' },
  { id: 'trunk', name: 'Trunk', overlay: 'trunk.png' },
  { id: 'engine', name: 'Engine', overlay: 'engine.png' }
];

// Spyne's S3 URLs for overlays (as discovered in forensic analysis)
const SPYNE_S3_OVERLAYS = {
  exterior: {
    'Front': 'https://spyne-static.s3.amazonaws.com/overlays/Front.png',
    'Right Front': 'https://spyne-static.s3.amazonaws.com/overlays/Right+Front.png',
    'Right Rear': 'https://spyne-static.s3.amazonaws.com/overlays/Right+Rear.png',
    'Left Front': 'https://spyne-static.s3.amazonaws.com/overlays/Left+Front.png',
    'Left Rear': 'https://spyne-static.s3.amazonaws.com/overlays/Left+Rear.png',
    'Rear': 'https://spyne-static.s3.amazonaws.com/overlays/Rear.png'
  },
  interior: {
    'Dashboard': 'https://spyne-test.s3.amazonaws.com/interiorOverlays/Dashboard.png',
    'Center dash': 'https://spyne-test.s3.amazonaws.com/interiorOverlays/Center+dash.png'
  },
  silhouettes: {
    'hatchback': (index: number) => 
      `https://spyne-cliq.s3.amazonaws.com/spyne-cliq/product/cars/hatchback/${index}.png`
  }
};

/**
 * GET /api/v1/overlays/config
 * Get overlay configuration for capture
 */
router.get('/config', [
  query('vehicleType').optional().isIn(VEHICLE_TYPES),
  query('angleCount').optional().isInt({ min: 8, max: 36 })
], async (req: Request, res: Response) => {
  try {
    const vehicleType = (req.query.vehicleType as string) || 'sedan';
    const angleCount = parseInt(req.query.angleCount as string) || 8;
    
    res.json({
      success: true,
      data: {
        vehicleType,
        angleCount,
        exteriorAngles: EXTERIOR_ANGLES,
        interiorOverlays: INTERIOR_OVERLAYS,
        supportedVehicleTypes: VEHICLE_TYPES
      }
    });
  } catch (error) {
    logger.error('Error getting overlay config:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/overlays/exterior
 * Get exterior overlay URLs
 */
router.get('/exterior', [
  query('vehicleType').optional().isIn(VEHICLE_TYPES),
  query('angleIndex').optional().isInt({ min: 0, max: 35 })
], async (req: Request, res: Response) => {
  try {
    const vehicleType = (req.query.vehicleType as string) || 'sedan';
    const angleIndex = req.query.angleIndex !== undefined 
      ? parseInt(req.query.angleIndex as string) 
      : undefined;
    
    let overlays;
    
    if (angleIndex !== undefined) {
      // Single angle
      const angle = EXTERIOR_ANGLES.find(a => a.id === angleIndex);
      if (!angle) {
        return res.status(404).json({
          success: false,
          error: { message: 'Angle not found' }
        });
      }
      
      overlays = [{
        ...angle,
        silhouetteUrl: `/assets/silhouettes/${vehicleType}/${angle.id}.png`,
        overlayUrl: `/assets/overlays/exterior/${angle.overlay}`
      }];
    } else {
      // All angles
      overlays = EXTERIOR_ANGLES.map(angle => ({
        ...angle,
        silhouetteUrl: `/assets/silhouettes/${vehicleType}/${angle.id}.png`,
        overlayUrl: `/assets/overlays/exterior/${angle.overlay}`
      }));
    }
    
    res.json({
      success: true,
      data: {
        vehicleType,
        overlays
      }
    });
  } catch (error) {
    logger.error('Error getting exterior overlays:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/overlays/interior
 * Get interior overlay URLs
 */
router.get('/interior', async (req: Request, res: Response) => {
  try {
    const overlays = INTERIOR_OVERLAYS.map(overlay => ({
      ...overlay,
      overlayUrl: `/assets/overlays/interior/${overlay.overlay}`
    }));
    
    res.json({
      success: true,
      data: { overlays }
    });
  } catch (error) {
    logger.error('Error getting interior overlays:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/overlays/silhouettes/:vehicleType
 * Get all silhouettes for a vehicle type
 */
router.get('/silhouettes/:vehicleType', async (req: Request, res: Response) => {
  try {
    const { vehicleType } = req.params;
    
    if (!VEHICLE_TYPES.includes(vehicleType)) {
      return res.status(400).json({
        success: false,
        error: { message: 'Invalid vehicle type' }
      });
    }
    
    const silhouettes = EXTERIOR_ANGLES.map((angle, index) => ({
      angleIndex: index,
      angleName: angle.name,
      url: `/assets/silhouettes/${vehicleType}/${index}.png`
    }));
    
    res.json({
      success: true,
      data: {
        vehicleType,
        silhouettes
      }
    });
  } catch (error) {
    logger.error('Error getting silhouettes:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/overlays/spyne-reference
 * Get reference URLs from Spyne's S3 (for development/testing)
 */
router.get('/spyne-reference', async (req: Request, res: Response) => {
  try {
    res.json({
      success: true,
      data: {
        note: 'These are Spyne\'s actual S3 URLs discovered via forensic analysis',
        overlays: SPYNE_S3_OVERLAYS
      }
    });
  } catch (error) {
    logger.error('Error getting Spyne reference:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/overlays/backgrounds
 * Get available background presets
 */
router.get('/backgrounds', async (req: Request, res: Response) => {
  try {
    const backgrounds = [
      {
        id: 'studio_white',
        name: 'Studio White',
        description: 'Clean white studio background',
        preview: '/assets/backgrounds/studio_white_preview.jpg'
      },
      {
        id: 'studio_grey',
        name: 'Studio Grey',
        description: 'Elegant grey studio background',
        preview: '/assets/backgrounds/studio_grey_preview.jpg'
      },
      {
        id: 'studio_dark',
        name: 'Studio Dark',
        description: 'Dramatic dark studio background',
        preview: '/assets/backgrounds/studio_dark_preview.jpg'
      },
      {
        id: 'showroom',
        name: 'Showroom',
        description: 'Dealership showroom style',
        preview: '/assets/backgrounds/showroom_preview.jpg'
      },
      {
        id: 'dealership',
        name: 'Dealership Floor',
        description: 'Realistic dealership floor',
        preview: '/assets/backgrounds/dealership_preview.jpg'
      },
      {
        id: 'outdoor_neutral',
        name: 'Outdoor Neutral',
        description: 'Neutral outdoor setting',
        preview: '/assets/backgrounds/outdoor_preview.jpg'
      }
    ];
    
    res.json({
      success: true,
      data: { backgrounds }
    });
  } catch (error) {
    logger.error('Error getting backgrounds:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

export default router;

