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

export interface ApiOrganization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface ApiUser {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  updated_at: string;
}

export interface ApiMembership {
  id: string;
  organization_id: string;
  user_id: string;
  role: 'admin' | 'member' | 'analyst';
  created_at: string;
  updated_at: string;
  user?: ApiUser;
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

  async post<T>(endpoint: string, body: unknown, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify(body),
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  async patch<T>(endpoint: string, body: unknown, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify(body),
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  async delete(endpoint: string, options?: RequestInit): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
  },

  async checkHealth(): Promise<HealthCheckResponse> {
    return this.get<HealthCheckResponse>('/health');
  },

  // Organizations API
  organizations: {
    list: () => apiClient.get<ApiOrganization[]>('/organizations'),
    get: (id: string) => apiClient.get<ApiOrganization>(`/organizations/${id}`),
    create: (data: { name: string; slug?: string }) =>
      apiClient.post<ApiOrganization>('/organizations', data),
    update: (id: string, data: { name?: string; slug?: string }) =>
      apiClient.patch<ApiOrganization>(`/organizations/${id}`, data),
  },

  // Users API
  users: {
    list: () => apiClient.get<ApiUser[]>('/users'),
    get: (id: string) => apiClient.get<ApiUser>(`/users/${id}`),
    create: (data: { email: string; full_name: string }) =>
      apiClient.post<ApiUser>('/users', data),
  },

  // Memberships API
  memberships: {
    list: (orgId: string) =>
      apiClient.get<ApiMembership[]>(`/organizations/${orgId}/members`),
    add: (orgId: string, data: { user_id: string; role?: 'admin' | 'member' | 'analyst' }) =>
      apiClient.post<ApiMembership>(`/organizations/${orgId}/members`, data),
    updateRole: (orgId: string, membershipId: string, role: 'admin' | 'member' | 'analyst') =>
      apiClient.patch<ApiMembership>(`/organizations/${orgId}/members/${membershipId}`, { role }),
    remove: (orgId: string, membershipId: string) =>
      apiClient.delete(`/organizations/${orgId}/members/${membershipId}`),
  },
};
