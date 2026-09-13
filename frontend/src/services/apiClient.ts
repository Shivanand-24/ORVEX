/**
 * ORVEX Base API Client
 *
 * Provides central fetch configuration and utility methods for communicating with
 * the ORVEX FastAPI backend service foundation.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
}

export const apiClient = {
  baseUrl: API_BASE_URL,

  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  async checkHealth(): Promise<HealthCheckResponse> {
    return this.get<HealthCheckResponse>('/health');
  },
};
