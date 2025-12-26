/**
 * API Client - Clone Spyne Web
 * ============================
 * Frontend API client for communicating with the backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  type: string;
  status: string;
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
  status: string;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data: ApiResponse<T> = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error?.message || 'Request failed');
    }

    return data.data as T;
  }

  // Vehicles
  async getVehicles(params?: {
    status?: string;
    type?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ vehicles: Vehicle[]; pagination: any }> {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`/vehicles${query ? `?${query}` : ''}`);
  }

  async getVehicle(id: string): Promise<{ vehicle: Vehicle }> {
    return this.request(`/vehicles/${id}`);
  }

  async createVehicle(vehicle: {
    make: string;
    model: string;
    year: number;
    type: string;
  }): Promise<{ vehicle: Vehicle }> {
    return this.request('/vehicles', {
      method: 'POST',
      body: JSON.stringify(vehicle),
    });
  }

  async updateVehicle(
    id: string,
    updates: Partial<Vehicle>
  ): Promise<{ vehicle: Vehicle }> {
    return this.request(`/vehicles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteVehicle(id: string): Promise<void> {
    return this.request(`/vehicles/${id}`, {
      method: 'DELETE',
    });
  }

  async get360Data(id: string): Promise<{
    vehicleId: string;
    vehicleName: string;
    images: { index: number; name: string; url: string }[];
    isComplete: boolean;
  }> {
    return this.request(`/vehicles/${id}/360`);
  }

  // Images
  async getVehicleImages(vehicleId: string): Promise<{ images: VehicleImage[] }> {
    return this.request(`/images/vehicle/${vehicleId}`);
  }

  // Processing
  async startProcessing(
    vehicleId: string,
    options?: {
      backgroundPreset?: string;
      addReflection?: boolean;
      addShadows?: boolean;
    }
  ): Promise<{ jobId: string }> {
    return this.request('/process/batch', {
      method: 'POST',
      body: JSON.stringify({
        vehicleId,
        options,
      }),
    });
  }

  async getProcessingStatus(jobId: string): Promise<{
    status: string;
    progress: number;
    result?: any;
  }> {
    return this.request(`/process/job/${jobId}`);
  }

  async getProcessingPresets(): Promise<{
    backgroundPresets: string[];
    outputSizes: { name: string; size: number[] }[];
  }> {
    return this.request('/process/presets');
  }

  // Overlays
  async getOverlayConfig(): Promise<{
    exteriorAngles: any[];
    interiorOverlays: any[];
    supportedVehicleTypes: string[];
  }> {
    return this.request('/overlays/config');
  }

  async getBackgrounds(): Promise<{
    backgrounds: { id: string; name: string; preview: string }[];
  }> {
    return this.request('/overlays/backgrounds');
  }
}

export const api = new ApiClient();
export default api;

