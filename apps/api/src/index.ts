/**
 * Clone Spyne API - Main Entry Point
 * ===================================
 * Backend server for the 360° car photography platform.
 * 
 * Features:
 * - Vehicle management (CRUD)
 * - Image upload and processing
 * - S3 integration for storage
 * - Background job queue for processing
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config();

// Import routes
import vehiclesRouter from './routes/vehicles';
import imagesRouter from './routes/images';
import overlaysRouter from './routes/overlays';
import processRouter from './routes/process';

// Import services
import { logger } from './services/logger.service';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Static files (for local development)
app.use('/assets', express.static(path.join(__dirname, '../../assets')));

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'clone-spyne-api',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// API Routes
app.use('/api/v1/vehicles', vehiclesRouter);
app.use('/api/v1/images', imagesRouter);
app.use('/api/v1/overlays', overlaysRouter);
app.use('/api/v1/process', processRouter);

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error:', err);
  
  res.status(err.status || 500).json({
    success: false,
    error: {
      message: err.message || 'Internal Server Error',
      code: err.code || 'INTERNAL_ERROR'
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: {
      message: 'Endpoint not found',
      code: 'NOT_FOUND'
    }
  });
});

// Start server
app.listen(PORT, () => {
  logger.info(`🚗 Clone Spyne API running on port ${PORT}`);
  logger.info(`   Environment: ${process.env.NODE_ENV || 'development'}`);
  logger.info(`   Health check: http://localhost:${PORT}/health`);
});

export default app;

