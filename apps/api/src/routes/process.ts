/**
 * Process Router
 * ==============
 * Image processing endpoints.
 * Handles triggering and monitoring of processing jobs.
 */

import { Router, Request, Response } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import { logger } from '../services/logger.service';
import { queueService, ProcessImageJob, BatchProcessJob } from '../services/queue.service';
import { processingService } from '../services/processing.service';

const router = Router();

/**
 * POST /api/v1/process/single
 * Process a single image
 */
router.post('/single', [
  body('vehicleId').isUUID(),
  body('imageId').isUUID(),
  body('inputUrl').isURL(),
  body('angleIndex').isInt({ min: 0, max: 35 }),
  body('options.backgroundPreset').optional().isString(),
  body('options.addReflection').optional().isBoolean(),
  body('options.addShadows').optional().isBoolean(),
  body('options.outputSize').optional().isArray()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const { vehicleId, imageId, inputUrl, angleIndex, options = {} } = req.body;
    
    const job: ProcessImageJob = {
      vehicleId,
      imageId,
      inputUrl,
      angleIndex,
      options: {
        backgroundPreset: options.backgroundPreset || 'studio_white',
        addReflection: options.addReflection !== false,
        addShadows: options.addShadows !== false,
        outputSize: options.outputSize || [1920, 1080]
      }
    };
    
    const jobId = await queueService.addProcessingJob(job);
    
    logger.info(`Processing job queued: ${jobId} for image ${imageId}`);
    
    res.status(202).json({
      success: true,
      data: {
        jobId,
        status: 'queued',
        message: 'Processing job has been queued'
      }
    });
  } catch (error) {
    logger.error('Error queuing processing job:', error);
    res.status(500).json({ success: false, error: { message: 'Failed to queue job' } });
  }
});

/**
 * POST /api/v1/process/batch
 * Process multiple images for a vehicle
 */
router.post('/batch', [
  body('vehicleId').isUUID(),
  body('images').isArray({ min: 1 }),
  body('images.*.imageId').isUUID(),
  body('images.*.inputUrl').isURL(),
  body('images.*.angleIndex').isInt({ min: 0, max: 35 }),
  body('options.backgroundPreset').optional().isString(),
  body('options.addReflection').optional().isBoolean(),
  body('options.addShadows').optional().isBoolean()
], async (req: Request, res: Response) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  
  try {
    const { vehicleId, images, options = {} } = req.body;
    
    const job: BatchProcessJob = {
      vehicleId,
      images,
      options: {
        backgroundPreset: options.backgroundPreset || 'studio_white',
        addReflection: options.addReflection !== false,
        addShadows: options.addShadows !== false,
        outputSize: options.outputSize || [1920, 1080]
      }
    };
    
    const jobId = await queueService.addBatchJob(job);
    
    logger.info(`Batch job queued: ${jobId} for vehicle ${vehicleId} (${images.length} images)`);
    
    res.status(202).json({
      success: true,
      data: {
        jobId,
        status: 'queued',
        imageCount: images.length,
        message: 'Batch processing job has been queued'
      }
    });
  } catch (error) {
    logger.error('Error queuing batch job:', error);
    res.status(500).json({ success: false, error: { message: 'Failed to queue batch job' } });
  }
});

/**
 * GET /api/v1/process/job/:jobId
 * Get job status
 */
router.get('/job/:jobId', async (req: Request, res: Response) => {
  try {
    const { jobId } = req.params;
    
    const status = await queueService.getJobStatus(jobId);
    
    if (status.status === 'not_found') {
      return res.status(404).json({
        success: false,
        error: { message: 'Job not found' }
      });
    }
    
    res.json({
      success: true,
      data: {
        jobId,
        ...status
      }
    });
  } catch (error) {
    logger.error('Error getting job status:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/process/queue/stats
 * Get queue statistics
 */
router.get('/queue/stats', async (req: Request, res: Response) => {
  try {
    const stats = await queueService.getQueueStats();
    
    res.json({
      success: true,
      data: { queue: stats }
    });
  } catch (error) {
    logger.error('Error getting queue stats:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/process/presets
 * Get available processing presets
 */
router.get('/presets', async (req: Request, res: Response) => {
  try {
    const presets = processingService.getAvailablePresets();
    
    res.json({
      success: true,
      data: {
        backgroundPresets: presets,
        outputSizes: [
          { name: 'HD', size: [1280, 720] },
          { name: 'Full HD', size: [1920, 1080] },
          { name: '2K', size: [2560, 1440] },
          { name: '4K', size: [3840, 2160] }
        ],
        defaultOptions: {
          backgroundPreset: 'studio_white',
          addReflection: true,
          addShadows: true,
          outputSize: [1920, 1080],
          quality: 95
        }
      }
    });
  } catch (error) {
    logger.error('Error getting presets:', error);
    res.status(500).json({ success: false, error: { message: 'Internal error' } });
  }
});

/**
 * GET /api/v1/process/health
 * Check processing system health
 */
router.get('/health', async (req: Request, res: Response) => {
  try {
    const pythonCheck = await processingService.checkPythonEnvironment();
    const queueStats = await queueService.getQueueStats();
    
    const healthy = pythonCheck.ready;
    
    res.status(healthy ? 200 : 503).json({
      success: true,
      data: {
        healthy,
        python: pythonCheck,
        queue: queueStats
      }
    });
  } catch (error) {
    logger.error('Error checking health:', error);
    res.status(503).json({ 
      success: false, 
      data: { healthy: false, error: (error as Error).message }
    });
  }
});

/**
 * POST /api/v1/process/test
 * Test processing with a sample image
 */
router.post('/test', [
  body('inputUrl').optional().isURL(),
  body('backgroundPreset').optional().isString()
], async (req: Request, res: Response) => {
  try {
    // Use a sample image if not provided
    const inputUrl = req.body.inputUrl || 
      'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800';
    
    const backgroundPreset = req.body.backgroundPreset || 'studio_white';
    
    const result = await processingService.processImage(
      inputUrl,
      'test-vehicle',
      0,
      {
        backgroundPreset,
        addReflection: true,
        addShadows: true,
        outputSize: [1920, 1080]
      }
    );
    
    res.json({
      success: result.success,
      data: result
    });
  } catch (error) {
    logger.error('Error in test processing:', error);
    res.status(500).json({ success: false, error: { message: (error as Error).message } });
  }
});

/**
 * POST /api/v1/process/direct
 * Direct synchronous processing - accepts base64 image and returns processed image
 * Used for testing the full pipeline
 */
router.post('/direct', async (req: Request, res: Response) => {
  try {
    const { 
      image,  // base64 encoded image
      backgroundPreset = 'studio_white',
      addReflection = true,
      addShadows = true,
      outputWidth = 1920,
      outputHeight = 1080
    } = req.body;
    
    if (!image) {
      return res.status(400).json({ 
        success: false, 
        error: { message: 'No image provided. Send base64 image in "image" field.' } 
      });
    }
    
    logger.info(`Direct processing request: preset=${backgroundPreset}, reflection=${addReflection}, shadows=${addShadows}`);
    
    const result = await processingService.processImageDirect(
      image,
      {
        backgroundPreset,
        addReflection,
        addShadows,
        outputSize: [outputWidth, outputHeight]
      }
    );
    
    res.json({
      success: result.success,
      data: result
    });
  } catch (error) {
    logger.error('Error in direct processing:', error);
    res.status(500).json({ success: false, error: { message: (error as Error).message } });
  }
});

export default router;

