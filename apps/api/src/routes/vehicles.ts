/**
 * Vehicles Router
 * ===============
 * CRUD operations for vehicles (inventory management).
 * Replicates Spyne's inventory API endpoints.
 */

import { Router, Request, Response } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../services/logger.service';

const router = Router();

// In-memory storage (replace with database in production)
interface Vehicle {
  id: string;
  vin?: string;
  make: string;
  model: string;
  year: number;
  color?: string;
  type: 'sedan' | 'suv' | 'hatchback' | 'truck' | 'coupe' | 'other';
  status: 'pending' | 'capturing' | 'processing' | 'completed';
  images: VehicleImage[];
  createdAt: string;
  updatedAt: string;
}

interface VehicleImage {
  id: string;
  angleIndex: number;
  angleName: string;
  inputUrl?: string;
  processedUrl?: string;
  status: 'pending' | 'uploaded' | 'processing' | 'completed' | 'failed';
  createdAt: string;
}

// In-memory database
const vehicles: Map<string, Vehicle> = new Map();

// Angle configuration (like Spyne's 8-point or 36-point capture)
const ANGLES_8 = [
  { index: 0, name: 'Front', angle: 0 },
  { index: 1, name: 'Front Right', angle: 45 },
  { index: 2, name: 'Right', angle: 90 },
  { index: 3, name: 'Rear Right', angle: 135 },
  { index: 4, name: 'Rear', angle: 180 },
  { index: 5, name: 'Rear Left', angle: 225 },
  { index: 6, name: 'Left', angle: 270 },
  { index: 7, name: 'Front Left', angle: 315 }
];

/**
 * GET /api/v1/vehicles
 * List all vehicles with optional filtering
 */
router.get('/', [
  query('status').optional().isIn(['pending', 'capturing', 'processing', 'completed']),
  query('type').optional().isIn(['sedan', 'suv', 'hatchback', 'truck', 'coupe', 'other']),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('offset').optional().isInt({ min: 0 })
], async (req: Request, res: Response) => {
  try {
    let results = Array.from(vehicles.values());
    
    // Filter by status
    if (req.query.status) {
      results = results.filter(v => v.status === req.query.status);
    }
    
    // Filter by type
    if (req.query.type) {
      results = results.filter(v => v.type === req.query.type);
    }
    
    // Pagination
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    
    const total = results.length;
    results = results.slice(offset, offset + limit);
    
    res.json({
      success: true,
      data: {
        vehicles: results,
        pagination: {
          total,
          limit,
          offset,
          hasMore: offset + limit < total
        }
      }
    });
  } catch (error) {
    logger.error('Error listing vehicles:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * POST /api/v1/vehicles
 * Create a new vehicle
 */
router.post('/', [
  body('make').trim().notEmpty().withMessage('Make is required'),
  body('model').trim().notEmpty().withMessage('Model is required'),
  body('year').isInt({ min: 1900, max: 2030 }).withMessage('Valid year required'),
  body('type').isIn(['sedan', 'suv', 'hatchback', 'truck', 'coupe', 'other']),
  body('vin').optional().trim(),
  body('color').optional().trim(),
  body('angleCount').optional().isInt({ min: 8, max: 36 })
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const { make, model, year, type, vin, color, angleCount = 8 } = req.body;
    
    const vehicleId = uuidv4();
    const now = new Date().toISOString();
    
    // Create image slots for each angle
    const images: VehicleImage[] = ANGLES_8.map((angle) => ({
      id: uuidv4(),
      angleIndex: angle.index,
      angleName: angle.name,
      status: 'pending',
      createdAt: now
    }));
    
    const vehicle: Vehicle = {
      id: vehicleId,
      vin,
      make,
      model,
      year,
      color,
      type,
      status: 'pending',
      images,
      createdAt: now,
      updatedAt: now
    };
    
    vehicles.set(vehicleId, vehicle);
    logger.info(`Created vehicle: ${vehicleId} - ${make} ${model}`);
    
    res.status(201).json({
      success: true,
      data: { vehicle }
    });
  } catch (error) {
    logger.error('Error creating vehicle:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/vehicles/:id
 * Get vehicle details
 */
router.get('/:id', [
  param('id').isUUID()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const vehicle = vehicles.get(req.params.id);
    
    if (!vehicle) {
      return res.status(404).json({
        success: false,
        error: { message: 'Vehicle not found', code: 'NOT_FOUND' }
      });
    }
    
    res.json({
      success: true,
      data: { vehicle }
    });
  } catch (error) {
    logger.error('Error getting vehicle:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * PATCH /api/v1/vehicles/:id
 * Update vehicle details
 */
router.patch('/:id', [
  param('id').isUUID(),
  body('make').optional().trim().notEmpty(),
  body('model').optional().trim().notEmpty(),
  body('year').optional().isInt({ min: 1900, max: 2030 }),
  body('type').optional().isIn(['sedan', 'suv', 'hatchback', 'truck', 'coupe', 'other']),
  body('status').optional().isIn(['pending', 'capturing', 'processing', 'completed'])
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const vehicle = vehicles.get(req.params.id);
    
    if (!vehicle) {
      return res.status(404).json({
        success: false,
        error: { message: 'Vehicle not found', code: 'NOT_FOUND' }
      });
    }
    
    // Update allowed fields
    const allowedFields = ['make', 'model', 'year', 'type', 'vin', 'color', 'status'];
    for (const field of allowedFields) {
      if (req.body[field] !== undefined) {
        (vehicle as any)[field] = req.body[field];
      }
    }
    
    vehicle.updatedAt = new Date().toISOString();
    vehicles.set(req.params.id, vehicle);
    
    logger.info(`Updated vehicle: ${req.params.id}`);
    
    res.json({
      success: true,
      data: { vehicle }
    });
  } catch (error) {
    logger.error('Error updating vehicle:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * DELETE /api/v1/vehicles/:id
 * Delete a vehicle
 */
router.delete('/:id', [
  param('id').isUUID()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const vehicle = vehicles.get(req.params.id);
    
    if (!vehicle) {
      return res.status(404).json({
        success: false,
        error: { message: 'Vehicle not found', code: 'NOT_FOUND' }
      });
    }
    
    vehicles.delete(req.params.id);
    logger.info(`Deleted vehicle: ${req.params.id}`);
    
    res.json({
      success: true,
      data: { message: 'Vehicle deleted successfully' }
    });
  } catch (error) {
    logger.error('Error deleting vehicle:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/vehicles/:id/360
 * Get 360° view data (processed images for viewer)
 */
router.get('/:id/360', [
  param('id').isUUID()
], async (req: Request, res: Response) => {
  try {
    const vehicle = vehicles.get(req.params.id);
    
    if (!vehicle) {
      return res.status(404).json({
        success: false,
        error: { message: 'Vehicle not found', code: 'NOT_FOUND' }
      });
    }
    
    // Get completed images
    const completedImages = vehicle.images
      .filter(img => img.status === 'completed' && img.processedUrl)
      .sort((a, b) => a.angleIndex - b.angleIndex)
      .map(img => ({
        index: img.angleIndex,
        name: img.angleName,
        url: img.processedUrl
      }));
    
    res.json({
      success: true,
      data: {
        vehicleId: vehicle.id,
        vehicleName: `${vehicle.year} ${vehicle.make} ${vehicle.model}`,
        totalAngles: vehicle.images.length,
        completedAngles: completedImages.length,
        isComplete: completedImages.length === vehicle.images.length,
        images: completedImages
      }
    });
  } catch (error) {
    logger.error('Error getting 360 data:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

export default router;

