/**
 * Images Router
 * =============
 * Image upload and management endpoints.
 * Handles pre-signed URLs and upload tracking.
 */

import { Router, Request, Response } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import multer from 'multer';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../services/logger.service';
import { s3Service } from '../services/s3.service';

const router = Router();

// Multer configuration for direct uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB max
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only JPEG, PNG, and WebP are allowed.'));
    }
  }
});

// In-memory image tracking
interface ImageRecord {
  id: string;
  vehicleId: string;
  angleIndex: number;
  filename: string;
  contentType: string;
  size?: number;
  inputUrl?: string;
  processedUrl?: string;
  status: 'pending' | 'uploading' | 'uploaded' | 'processing' | 'completed' | 'failed';
  uploadedAt?: string;
  processedAt?: string;
  error?: string;
}

const images: Map<string, ImageRecord> = new Map();

/**
 * POST /api/v1/images/presigned-url
 * Get pre-signed URL for direct S3 upload
 */
router.post('/presigned-url', [
  body('vehicleId').isUUID(),
  body('angleIndex').isInt({ min: 0, max: 35 }),
  body('filename').trim().notEmpty(),
  body('contentType').isIn(['image/jpeg', 'image/png', 'image/webp'])
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const { vehicleId, angleIndex, filename, contentType } = req.body;
    
    // Generate pre-signed URL
    const { uploadUrl, key, publicUrl } = await s3Service.getUploadUrl(
      `${vehicleId}/${angleIndex}/${filename}`,
      contentType
    );
    
    // Create image record
    const imageId = uuidv4();
    const record: ImageRecord = {
      id: imageId,
      vehicleId,
      angleIndex,
      filename,
      contentType,
      status: 'pending'
    };
    
    images.set(imageId, record);
    
    res.json({
      success: true,
      data: {
        imageId,
        uploadUrl,
        publicUrl,
        key,
        expiresIn: 3600
      }
    });
  } catch (error) {
    logger.error('Error generating presigned URL:', error);
    res.status(500).json({ success: false, error: { message: 'Failed to generate upload URL' } });
  }
});

/**
 * POST /api/v1/images/upload
 * Direct file upload (alternative to presigned URL)
 */
router.post('/upload', upload.single('image'), [
  body('vehicleId').isUUID(),
  body('angleIndex').isInt({ min: 0, max: 35 })
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  if (!req.file) {
    return res.status(400).json({ 
      success: false, 
      error: { message: 'No image file provided' } 
    });
  }
  
  try {
    const { vehicleId, angleIndex } = req.body;
    const file = req.file;
    
    // Generate unique filename
    const ext = file.originalname.split('.').pop() || 'jpg';
    const filename = `${uuidv4()}.${ext}`;
    const key = `uploads/${vehicleId}/${angleIndex}/${filename}`;
    
    // Upload to S3
    const publicUrl = await s3Service.uploadBuffer(
      file.buffer,
      key,
      file.mimetype
    );
    
    // Create image record
    const imageId = uuidv4();
    const record: ImageRecord = {
      id: imageId,
      vehicleId,
      angleIndex: parseInt(angleIndex),
      filename,
      contentType: file.mimetype,
      size: file.size,
      inputUrl: publicUrl,
      status: 'uploaded',
      uploadedAt: new Date().toISOString()
    };
    
    images.set(imageId, record);
    
    logger.info(`Image uploaded: ${imageId} for vehicle ${vehicleId}`);
    
    res.status(201).json({
      success: true,
      data: {
        imageId,
        url: publicUrl,
        vehicleId,
        angleIndex: parseInt(angleIndex)
      }
    });
  } catch (error) {
    logger.error('Error uploading image:', error);
    res.status(500).json({ success: false, error: { message: 'Upload failed' } });
  }
});

/**
 * POST /api/v1/images/:id/confirm
 * Confirm that upload to presigned URL completed
 */
router.post('/:id/confirm', [
  param('id').isUUID(),
  body('publicUrl').isURL()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const record = images.get(req.params.id);
    
    if (!record) {
      return res.status(404).json({
        success: false,
        error: { message: 'Image record not found' }
      });
    }
    
    record.inputUrl = req.body.publicUrl;
    record.status = 'uploaded';
    record.uploadedAt = new Date().toISOString();
    
    images.set(req.params.id, record);
    
    logger.info(`Upload confirmed: ${req.params.id}`);
    
    res.json({
      success: true,
      data: { image: record }
    });
  } catch (error) {
    logger.error('Error confirming upload:', error);
    res.status(500).json({ success: false, error: { message: 'Confirmation failed' } });
  }
});

/**
 * GET /api/v1/images/:id
 * Get image details
 */
router.get('/:id', [
  param('id').isUUID()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const record = images.get(req.params.id);
    
    if (!record) {
      return res.status(404).json({
        success: false,
        error: { message: 'Image not found' }
      });
    }
    
    res.json({
      success: true,
      data: { image: record }
    });
  } catch (error) {
    logger.error('Error getting image:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/images/vehicle/:vehicleId
 * Get all images for a vehicle
 */
router.get('/vehicle/:vehicleId', [
  param('vehicleId').isUUID()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const vehicleImages = Array.from(images.values())
      .filter(img => img.vehicleId === req.params.vehicleId)
      .sort((a, b) => a.angleIndex - b.angleIndex);
    
    res.json({
      success: true,
      data: { 
        vehicleId: req.params.vehicleId,
        images: vehicleImages,
        count: vehicleImages.length
      }
    });
  } catch (error) {
    logger.error('Error getting vehicle images:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * DELETE /api/v1/images/:id
 * Delete an image
 */
router.delete('/:id', [
  param('id').isUUID()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const record = images.get(req.params.id);
    
    if (!record) {
      return res.status(404).json({
        success: false,
        error: { message: 'Image not found' }
      });
    }
    
    // Delete from S3 if uploaded
    if (record.inputUrl) {
      try {
        const key = record.inputUrl.split('.com/')[1];
        await s3Service.deleteObject(key);
      } catch (e) {
        logger.warn('Failed to delete from S3:', e);
      }
    }
    
    images.delete(req.params.id);
    
    logger.info(`Image deleted: ${req.params.id}`);
    
    res.json({
      success: true,
      data: { message: 'Image deleted successfully' }
    });
  } catch (error) {
    logger.error('Error deleting image:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

export default router;

