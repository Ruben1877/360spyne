/**
 * Queue Service
 * =============
 * Bull-based job queue for image processing.
 * Handles background processing like Spyne does.
 */

import Bull from 'bull';
import { logger } from './logger.service';
import { processingService } from './processing.service';

// Queue configuration
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

// Create queues
export const imageProcessingQueue = new Bull('image-processing', REDIS_URL, {
  defaultJobOptions: {
    removeOnComplete: 100,
    removeOnFail: 50,
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    }
  }
});

// Job types
export interface ProcessImageJob {
  vehicleId: string;
  imageId: string;
  inputUrl: string;
  angleIndex: number;
  options: {
    backgroundPreset: string;
    addReflection: boolean;
    addShadows: boolean;
    outputSize: [number, number];
  };
}

export interface BatchProcessJob {
  vehicleId: string;
  images: {
    imageId: string;
    inputUrl: string;
    angleIndex: number;
  }[];
  options: {
    backgroundPreset: string;
    addReflection: boolean;
    addShadows: boolean;
    outputSize: [number, number];
  };
}

// Queue processors
imageProcessingQueue.process('process-single', async (job) => {
  const data = job.data as ProcessImageJob;
  logger.info(`Processing image: ${data.imageId} for vehicle: ${data.vehicleId}`);
  
  try {
    const result = await processingService.processImage(
      data.inputUrl,
      data.vehicleId,
      data.angleIndex,
      data.options
    );
    
    logger.info(`Completed processing: ${data.imageId}`);
    return result;
  } catch (error) {
    logger.error(`Failed to process image: ${data.imageId}`, error);
    throw error;
  }
});

imageProcessingQueue.process('process-batch', async (job) => {
  const data = job.data as BatchProcessJob;
  logger.info(`Processing batch for vehicle: ${data.vehicleId} (${data.images.length} images)`);
  
  const results = [];
  
  for (let i = 0; i < data.images.length; i++) {
    const image = data.images[i];
    
    try {
      await job.progress((i / data.images.length) * 100);
      
      const result = await processingService.processImage(
        image.inputUrl,
        data.vehicleId,
        image.angleIndex,
        data.options
      );
      
      results.push({ ...image, success: true, result });
    } catch (error) {
      results.push({ ...image, success: false, error: (error as Error).message });
    }
  }
  
  logger.info(`Batch complete for vehicle: ${data.vehicleId}`);
  return results;
});

// Queue events
imageProcessingQueue.on('completed', (job, result) => {
  logger.info(`Job ${job.id} completed`);
});

imageProcessingQueue.on('failed', (job, err) => {
  logger.error(`Job ${job.id} failed:`, err);
});

imageProcessingQueue.on('progress', (job, progress) => {
  logger.debug(`Job ${job.id} progress: ${progress}%`);
});

// Queue service class
export class QueueService {
  
  /**
   * Add a single image processing job
   */
  async addProcessingJob(job: ProcessImageJob): Promise<string> {
    const result = await imageProcessingQueue.add('process-single', job);
    return result.id?.toString() || '';
  }
  
  /**
   * Add a batch processing job
   */
  async addBatchJob(job: BatchProcessJob): Promise<string> {
    const result = await imageProcessingQueue.add('process-batch', job);
    return result.id?.toString() || '';
  }
  
  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<{
    status: string;
    progress: number;
    result?: any;
    error?: string;
  }> {
    const job = await imageProcessingQueue.getJob(jobId);
    
    if (!job) {
      return { status: 'not_found', progress: 0 };
    }
    
    const state = await job.getState();
    const progress = job.progress() as number;
    
    if (state === 'completed') {
      return { status: 'completed', progress: 100, result: job.returnvalue };
    }
    
    if (state === 'failed') {
      return { status: 'failed', progress, error: job.failedReason };
    }
    
    return { status: state, progress };
  }
  
  /**
   * Get queue statistics
   */
  async getQueueStats(): Promise<{
    waiting: number;
    active: number;
    completed: number;
    failed: number;
  }> {
    const [waiting, active, completed, failed] = await Promise.all([
      imageProcessingQueue.getWaitingCount(),
      imageProcessingQueue.getActiveCount(),
      imageProcessingQueue.getCompletedCount(),
      imageProcessingQueue.getFailedCount()
    ]);
    
    return { waiting, active, completed, failed };
  }
  
  /**
   * Clear completed jobs
   */
  async cleanCompleted(): Promise<void> {
    await imageProcessingQueue.clean(0, 'completed');
    logger.info('Cleaned completed jobs');
  }
}

export const queueService = new QueueService();
export default queueService;

