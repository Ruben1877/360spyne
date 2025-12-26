/**
 * API Service - Clone Spyne Mobile
 * =================================
 * Handles all API communication with the backend.
 */

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:3001';

interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  type: string;
  status: string;
  images: any[];
}

interface CreateVehicleRequest {
  make: string;
  model: string;
  year: number;
  type: string;
  vin?: string;
  color?: string;
}

interface UploadResponse {
  imageId: string;
  url: string;
  vehicleId: string;
  angleIndex: number;
}

class ApiService {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || 'Request failed');
    }

    return data.data;
  }

  // Vehicles
  async getVehicles(): Promise<{ vehicles: Vehicle[] }> {
    return this.request('/api/v1/vehicles');
  }

  async getVehicle(id: string): Promise<{ vehicle: Vehicle }> {
    return this.request(`/api/v1/vehicles/${id}`);
  }

  async createVehicle(vehicle: CreateVehicleRequest): Promise<{ vehicle: Vehicle }> {
    return this.request('/api/v1/vehicles', {
      method: 'POST',
      body: JSON.stringify(vehicle),
    });
  }

  async updateVehicle(id: string, updates: Partial<Vehicle>): Promise<{ vehicle: Vehicle }> {
    return this.request(`/api/v1/vehicles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  // Images
  async getPresignedUrl(
    vehicleId: string,
    angleIndex: number,
    filename: string,
    contentType: string
  ): Promise<{ imageId: string; uploadUrl: string; publicUrl: string }> {
    return this.request('/api/v1/images/presigned-url', {
      method: 'POST',
      body: JSON.stringify({
        vehicleId,
        angleIndex,
        filename,
        contentType,
      }),
    });
  }

  async uploadImage(
    vehicleId: string,
    angleIndex: number,
    imageUri: string
  ): Promise<UploadResponse> {
    // Create form data
    const formData = new FormData();
    formData.append('vehicleId', vehicleId);
    formData.append('angleIndex', angleIndex.toString());
    
    // Get filename from URI
    const filename = imageUri.split('/').pop() || 'image.jpg';
    
    formData.append('image', {
      uri: imageUri,
      name: filename,
      type: 'image/jpeg',
    } as any);

    const response = await fetch(`${this.baseUrl}/api/v1/images/upload`, {
      method: 'POST',
      headers: {
        ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || 'Upload failed');
    }

    return data.data;
  }

  async uploadMultipleImages(
    vehicleId: string,
    images: string[]
  ): Promise<UploadResponse[]> {
    const results: UploadResponse[] = [];

    for (let i = 0; i < images.length; i++) {
      const result = await this.uploadImage(vehicleId, i, images[i]);
      results.push(result);
    }

    return results;
  }

  // Processing
  async startProcessing(
    vehicleId: string,
    imageIds: string[],
    options?: {
      backgroundPreset?: string;
      addReflection?: boolean;
      addShadows?: boolean;
    }
  ): Promise<{ jobId: string }> {
    return this.request('/api/v1/process/batch', {
      method: 'POST',
      body: JSON.stringify({
        vehicleId,
        images: imageIds.map((id, index) => ({
          imageId: id,
          inputUrl: '', // Will be filled by backend
          angleIndex: index,
        })),
        options: {
          backgroundPreset: options?.backgroundPreset || 'studio_white',
          addReflection: options?.addReflection ?? true,
          addShadows: options?.addShadows ?? true,
        },
      }),
    });
  }

  async getProcessingStatus(jobId: string): Promise<{
    status: string;
    progress: number;
    result?: any;
  }> {
    return this.request(`/api/v1/process/job/${jobId}`);
  }

  // Overlays
  async getOverlays(vehicleType: string): Promise<{
    overlays: Array<{
      angleIndex: number;
      angleName: string;
      overlayUrl: string;
    }>;
  }> {
    return this.request(`/api/v1/overlays/exterior?vehicleType=${vehicleType}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

export const api = new ApiService();
export default api;

