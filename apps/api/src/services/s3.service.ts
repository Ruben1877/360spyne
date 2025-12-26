/**
 * S3 Service
 * ==========
 * AWS S3 integration for image storage.
 * Replicates Spyne's S3 usage patterns.
 */

import { 
  S3Client, 
  PutObjectCommand, 
  GetObjectCommand,
  DeleteObjectCommand,
  ListObjectsV2Command
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { v4 as uuidv4 } from 'uuid';
import { logger } from './logger.service';

// S3 Configuration
const s3Config = {
  region: process.env.AWS_REGION || 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || ''
  }
};

// Initialize S3 client
const s3Client = new S3Client(s3Config);

// Bucket names
const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'clone-spyne-uploads';
const PROCESSED_BUCKET = process.env.S3_PROCESSED_BUCKET || 'clone-spyne-processed';

export class S3Service {
  
  /**
   * Generate a pre-signed URL for upload
   */
  async getUploadUrl(
    filename: string,
    contentType: string,
    expiresIn: number = 3600
  ): Promise<{ uploadUrl: string; key: string; publicUrl: string }> {
    const key = `uploads/${uuidv4()}/${filename}`;
    
    const command = new PutObjectCommand({
      Bucket: BUCKET_NAME,
      Key: key,
      ContentType: contentType
    });
    
    const uploadUrl = await getSignedUrl(s3Client, command, { expiresIn });
    const publicUrl = `https://${BUCKET_NAME}.s3.amazonaws.com/${key}`;
    
    logger.info(`Generated upload URL for: ${filename}`);
    
    return { uploadUrl, key, publicUrl };
  }
  
  /**
   * Generate a pre-signed URL for download
   */
  async getDownloadUrl(key: string, expiresIn: number = 3600): Promise<string> {
    const command = new GetObjectCommand({
      Bucket: BUCKET_NAME,
      Key: key
    });
    
    return getSignedUrl(s3Client, command, { expiresIn });
  }
  
  /**
   * Upload a buffer directly to S3
   */
  async uploadBuffer(
    buffer: Buffer,
    key: string,
    contentType: string,
    bucket: string = BUCKET_NAME
  ): Promise<string> {
    const command = new PutObjectCommand({
      Bucket: bucket,
      Key: key,
      Body: buffer,
      ContentType: contentType
    });
    
    await s3Client.send(command);
    
    const publicUrl = `https://${bucket}.s3.amazonaws.com/${key}`;
    logger.info(`Uploaded to S3: ${key}`);
    
    return publicUrl;
  }
  
  /**
   * Upload processed image
   */
  async uploadProcessedImage(
    buffer: Buffer,
    vehicleId: string,
    angleIndex: number,
    format: string = 'jpg'
  ): Promise<string> {
    const key = `processed/${vehicleId}/${angleIndex}.${format}`;
    
    return this.uploadBuffer(buffer, key, `image/${format}`, PROCESSED_BUCKET);
  }
  
  /**
   * Get object from S3
   */
  async getObject(key: string, bucket: string = BUCKET_NAME): Promise<Buffer> {
    const command = new GetObjectCommand({
      Bucket: bucket,
      Key: key
    });
    
    const response = await s3Client.send(command);
    
    // Convert stream to buffer
    const chunks: Uint8Array[] = [];
    for await (const chunk of response.Body as any) {
      chunks.push(chunk);
    }
    
    return Buffer.concat(chunks);
  }
  
  /**
   * Delete object from S3
   */
  async deleteObject(key: string, bucket: string = BUCKET_NAME): Promise<void> {
    const command = new DeleteObjectCommand({
      Bucket: bucket,
      Key: key
    });
    
    await s3Client.send(command);
    logger.info(`Deleted from S3: ${key}`);
  }
  
  /**
   * List objects in a prefix
   */
  async listObjects(prefix: string, bucket: string = BUCKET_NAME): Promise<string[]> {
    const command = new ListObjectsV2Command({
      Bucket: bucket,
      Prefix: prefix
    });
    
    const response = await s3Client.send(command);
    
    return (response.Contents || []).map(obj => obj.Key!);
  }
  
  /**
   * Generate URLs for all processed images of a vehicle
   */
  async getProcessedImageUrls(vehicleId: string): Promise<string[]> {
    const prefix = `processed/${vehicleId}/`;
    const keys = await this.listObjects(prefix, PROCESSED_BUCKET);
    
    return keys.map(key => 
      `https://${PROCESSED_BUCKET}.s3.amazonaws.com/${key}`
    );
  }
}

export const s3Service = new S3Service();
export default s3Service;

