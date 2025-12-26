/**
 * Processing Service
 * ==================
 * Bridges Node.js API with Python processing scripts.
 * Calls the Python ML modules for image processing.
 */

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import os from 'os';
import { v4 as uuidv4 } from 'uuid';
import { logger } from './logger.service';
import { s3Service } from './s3.service';

export interface ProcessingOptions {
  backgroundPreset: string;
  addReflection: boolean;
  addShadows: boolean;
  outputSize: [number, number];
  quality?: number;
}

export interface ProcessingResult {
  success: boolean;
  outputUrl?: string;
  processingTime?: number;
  error?: string;
}

export class ProcessingService {
  private pythonPath: string;
  private scriptsPath: string;
  
  constructor() {
    // Python executable (use virtual env if available)
    this.pythonPath = process.env.PYTHON_PATH || 'python3';
    
    // Path to Python scripts
    this.scriptsPath = path.join(__dirname, '../../python');
  }
  
  /**
   * Process a single image using Python ML pipeline
   */
  async processImage(
    inputUrl: string,
    vehicleId: string,
    angleIndex: number,
    options: ProcessingOptions
  ): Promise<ProcessingResult> {
    const startTime = Date.now();
    const tempDir = path.join(os.tmpdir(), 'clone-spyne', uuidv4());
    
    try {
      // Create temp directory
      await fs.mkdir(tempDir, { recursive: true });
      
      const inputPath = path.join(tempDir, 'input.jpg');
      const outputPath = path.join(tempDir, 'output.jpg');
      
      // Download input image
      logger.info(`Downloading input image: ${inputUrl}`);
      await this.downloadImage(inputUrl, inputPath);
      
      // Run Python processing
      logger.info(`Processing with Python: ${inputPath}`);
      await this.runPythonProcessor(inputPath, outputPath, options);
      
      // Read output and upload to S3
      const outputBuffer = await fs.readFile(outputPath);
      const outputUrl = await s3Service.uploadProcessedImage(
        outputBuffer,
        vehicleId,
        angleIndex,
        'jpg'
      );
      
      const processingTime = Date.now() - startTime;
      logger.info(`Processing complete in ${processingTime}ms: ${outputUrl}`);
      
      return {
        success: true,
        outputUrl,
        processingTime
      };
      
    } catch (error) {
      logger.error('Processing failed:', error);
      return {
        success: false,
        error: (error as Error).message
      };
      
    } finally {
      // Cleanup temp files
      try {
        await fs.rm(tempDir, { recursive: true, force: true });
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  }
  
  /**
   * Download image from URL to local path
   */
  private async downloadImage(url: string, outputPath: string): Promise<void> {
    // If it's an S3 URL, use S3 service
    if (url.includes('s3.amazonaws.com')) {
      const key = url.split('.com/')[1];
      const buffer = await s3Service.getObject(key);
      await fs.writeFile(outputPath, buffer);
      return;
    }
    
    // Otherwise, fetch from URL
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to download image: ${response.status}`);
    }
    
    const buffer = Buffer.from(await response.arrayBuffer());
    await fs.writeFile(outputPath, buffer);
  }
  
  /**
   * Run Python processing script
   */
  private runPythonProcessor(
    inputPath: string,
    outputPath: string,
    options: ProcessingOptions
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(this.scriptsPath, 'process_image.py');
      
      const args = [
        scriptPath,
        inputPath,
        outputPath,
        '--preset', options.backgroundPreset,
        '--size', options.outputSize[0].toString(), options.outputSize[1].toString(),
        '--quality', (options.quality || 95).toString()
      ];
      
      if (!options.addReflection) {
        args.push('--no-reflection');
      }
      
      if (!options.addShadows) {
        args.push('--no-shadows');
      }
      
      logger.debug(`Running: ${this.pythonPath} ${args.join(' ')}`);
      
      const process = spawn(this.pythonPath, args, {
        cwd: this.scriptsPath,
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });
      
      let stdout = '';
      let stderr = '';
      
      process.stdout.on('data', (data) => {
        stdout += data.toString();
        logger.debug(`Python stdout: ${data}`);
      });
      
      process.stderr.on('data', (data) => {
        stderr += data.toString();
        logger.warn(`Python stderr: ${data}`);
      });
      
      process.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        }
      });
      
      process.on('error', (err) => {
        reject(new Error(`Failed to start Python process: ${err.message}`));
      });
    });
  }
  
  /**
   * Check if Python environment is ready
   */
  async checkPythonEnvironment(): Promise<{
    ready: boolean;
    pythonVersion?: string;
    error?: string;
  }> {
    return new Promise((resolve) => {
      const process = spawn(this.pythonPath, ['--version']);
      
      let version = '';
      
      process.stdout.on('data', (data) => {
        version += data.toString();
      });
      
      process.on('close', (code) => {
        if (code === 0) {
          resolve({ ready: true, pythonVersion: version.trim() });
        } else {
          resolve({ ready: false, error: 'Python not found' });
        }
      });
      
      process.on('error', (err) => {
        resolve({ ready: false, error: err.message });
      });
    });
  }
  
  /**
   * Get available background presets
   */
  getAvailablePresets(): string[] {
    return [
      'studio_white',
      'studio_grey',
      'studio_dark',
      'showroom',
      'dealership',
      'outdoor_neutral'
    ];
  }
  
  /**
   * Process image directly from base64 - returns processed image as base64
   * Used for testing and instant preview
   */
  async processImageDirect(
    base64Image: string,
    options: ProcessingOptions
  ): Promise<{
    success: boolean;
    processedImage?: string;
    processingTime?: number;
    stages?: Record<string, any>;
    error?: string;
  }> {
    const startTime = Date.now();
    const tempDir = path.join(os.tmpdir(), 'clone-spyne', uuidv4());
    
    try {
      // Create temp directory
      await fs.mkdir(tempDir, { recursive: true });
      
      const inputPath = path.join(tempDir, 'input.jpg');
      const outputPath = path.join(tempDir, 'output.jpg');
      
      // Decode base64 and save to file
      // Remove data URL prefix if present
      const base64Data = base64Image.replace(/^data:image\/\w+;base64,/, '');
      const imageBuffer = Buffer.from(base64Data, 'base64');
      await fs.writeFile(inputPath, imageBuffer);
      
      logger.info(`Processing image directly: ${inputPath}`);
      logger.info(`Options: preset=${options.backgroundPreset}, reflection=${options.addReflection}, shadows=${options.addShadows}`);
      
      // Run Python processing
      const pythonOutput = await this.runPythonProcessorWithOutput(inputPath, outputPath, options);
      
      // Read output and convert to base64
      const outputBuffer = await fs.readFile(outputPath);
      const outputBase64 = `data:image/jpeg;base64,${outputBuffer.toString('base64')}`;
      
      const processingTime = Date.now() - startTime;
      logger.info(`Direct processing complete in ${processingTime}ms`);
      
      return {
        success: true,
        processedImage: outputBase64,
        processingTime,
        stages: pythonOutput.stages
      };
      
    } catch (error) {
      logger.error('Direct processing failed:', error);
      return {
        success: false,
        error: (error as Error).message
      };
      
    } finally {
      // Cleanup temp files
      try {
        await fs.rm(tempDir, { recursive: true, force: true });
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  }
  
  /**
   * Run Python processing script and capture detailed output
   */
  private runPythonProcessorWithOutput(
    inputPath: string,
    outputPath: string,
    options: ProcessingOptions
  ): Promise<{ stages: Record<string, any> }> {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(this.scriptsPath, 'process_image.py');
      
      const args = [
        scriptPath,
        inputPath,
        outputPath,
        '--preset', options.backgroundPreset,
        '--size', options.outputSize[0].toString(), options.outputSize[1].toString(),
        '--quality', (options.quality || 95).toString()
      ];
      
      if (!options.addReflection) {
        args.push('--no-reflection');
      }
      
      if (!options.addShadows) {
        args.push('--no-shadows');
      }
      
      logger.debug(`Running: ${this.pythonPath} ${args.join(' ')}`);
      
      const proc = spawn(this.pythonPath, args, {
        cwd: this.scriptsPath,
        env: { ...process.env, PYTHONUNBUFFERED: '1' }
      });
      
      let stdout = '';
      let stderr = '';
      
      proc.stdout.on('data', (data) => {
        stdout += data.toString();
        logger.debug(`Python: ${data}`);
      });
      
      proc.stderr.on('data', (data) => {
        stderr += data.toString();
        // MediaPipe outputs info to stderr, not always errors
        logger.debug(`Python stderr: ${data}`);
      });
      
      proc.on('close', (code) => {
        if (code === 0) {
          // Parse stages from stdout if available
          const stages: Record<string, any> = {};
          const lines = stdout.split('\n');
          for (const line of lines) {
            if (line.includes('[') && line.includes('/8]')) {
              const match = line.match(/\[(\d)\/8\]\s+(.+)/);
              if (match) {
                stages[`step_${match[1]}`] = match[2];
              }
            }
          }
          resolve({ stages });
        } else {
          reject(new Error(`Python process exited with code ${code}: ${stderr || stdout}`));
        }
      });
      
      proc.on('error', (err) => {
        reject(new Error(`Failed to start Python process: ${err.message}`));
      });
    });
  }
}

export const processingService = new ProcessingService();
export default processingService;

