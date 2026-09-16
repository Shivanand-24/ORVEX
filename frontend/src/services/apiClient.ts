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

export interface ApiKnowledgeSource {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  document_count?: number;
}

export interface ApiKnowledgeDocument {
  id: string;
  organization_id: string;
  source_id: string;
  name: string;
  file_type: string;
  storage_path: string;
  size_bytes: number;
  processing_status: string;
  indexing_status: string;
  status: 'Pending' | 'Processing' | 'Processed' | 'Failed';
  readiness: 'NotIndexed' | 'Indexing' | 'Indexed' | 'IndexFailed';
  summary?: string | null;
  created_at: string;
  updated_at: string;
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

  // Knowledge API
  knowledge: {
    sources: {
      list: (params?: { organization_id?: string; skip?: number; limit?: number }) => {
        const query = new URLSearchParams();
        if (params?.organization_id) query.append('organization_id', params.organization_id);
        if (params?.skip !== undefined) query.append('skip', String(params.skip));
        if (params?.limit !== undefined) query.append('limit', String(params.limit));
        const qs = query.toString();
        return apiClient.get<ApiKnowledgeSource[]>(qs ? `/knowledge/sources?${qs}` : '/knowledge/sources');
      },
      get: (sourceId: string, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.get<ApiKnowledgeSource>(`/knowledge/sources/${sourceId}${qs}`);
      },
      create: (data: { organization_id: string; name: string; description?: string }) =>
        apiClient.post<ApiKnowledgeSource>('/knowledge/sources', data),
      update: (sourceId: string, data: { name?: string; description?: string }, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.patch<ApiKnowledgeSource>(`/knowledge/sources/${sourceId}${qs}`, data);
      },
      delete: (sourceId: string, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.delete(`/knowledge/sources/${sourceId}${qs}`);
      },
    },
    documents: {
      list: (sourceId: string, params?: { organization_id?: string; skip?: number; limit?: number }) => {
        const query = new URLSearchParams();
        if (params?.organization_id) query.append('organization_id', params.organization_id);
        if (params?.skip !== undefined) query.append('skip', String(params.skip));
        if (params?.limit !== undefined) query.append('limit', String(params.limit));
        const qs = query.toString();
        return apiClient.get<ApiKnowledgeDocument[]>(qs ? `/knowledge/sources/${sourceId}/documents?${qs}` : `/knowledge/sources/${sourceId}/documents`);
      },
      get: (documentId: string, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.get<ApiKnowledgeDocument>(`/knowledge/documents/${documentId}${qs}`);
      },
      create: (sourceId: string, data: {
        name: string;
        file_type?: string;
        storage_path?: string;
        size_bytes?: number;
        summary?: string;
        organization_id?: string;
        status?: string;
        readiness?: string;
      }, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.post<ApiKnowledgeDocument>(`/knowledge/sources/${sourceId}/documents${qs}`, data);
      },
      update: (documentId: string, data: {
        name?: string;
        file_type?: string;
        storage_path?: string;
        size_bytes?: number;
        summary?: string;
        processing_status?: string;
        indexing_status?: string;
        status?: string;
        readiness?: string;
      }, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.patch<ApiKnowledgeDocument>(`/knowledge/documents/${documentId}${qs}`, data);
      },
      delete: (documentId: string, params?: { organization_id?: string }) => {
        const qs = params?.organization_id ? `?organization_id=${encodeURIComponent(params.organization_id)}` : '';
        return apiClient.delete(`/knowledge/documents/${documentId}${qs}`);
      },
    },
  },

  // Knowledge top-level convenience methods
  createKnowledgeSource: (data: { organization_id: string; name: string; description?: string }) =>
    apiClient.knowledge.sources.create(data),
  getKnowledgeSources: (params?: { organization_id?: string; skip?: number; limit?: number }) =>
    apiClient.knowledge.sources.list(params),
  getKnowledgeSource: (sourceId: string, params?: { organization_id?: string }) =>
    apiClient.knowledge.sources.get(sourceId, params),
  updateKnowledgeSource: (sourceId: string, data: { name?: string; description?: string }, params?: { organization_id?: string }) =>
    apiClient.knowledge.sources.update(sourceId, data, params),
  deleteKnowledgeSource: (sourceId: string, params?: { organization_id?: string }) =>
    apiClient.knowledge.sources.delete(sourceId, params),
  createKnowledgeDocument: (sourceId: string, data: {
    name: string;
    file_type?: string;
    storage_path?: string;
    size_bytes?: number;
    summary?: string;
    organization_id?: string;
    status?: string;
    readiness?: string;
  }, params?: { organization_id?: string }) =>
    apiClient.knowledge.documents.create(sourceId, data, params),
  getKnowledgeDocuments: (sourceId: string, params?: { organization_id?: string; skip?: number; limit?: number }) =>
    apiClient.knowledge.documents.list(sourceId, params),
  getKnowledgeDocument: (documentId: string, params?: { organization_id?: string }) =>
    apiClient.knowledge.documents.get(documentId, params),
  updateKnowledgeDocument: (documentId: string, data: {
    name?: string;
    file_type?: string;
    storage_path?: string;
    size_bytes?: number;
    summary?: string;
    processing_status?: string;
    indexing_status?: string;
    status?: string;
    readiness?: string;
  }, params?: { organization_id?: string }) =>
    apiClient.knowledge.documents.update(documentId, data, params),
  deleteKnowledgeDocument: (documentId: string, params?: { organization_id?: string }) =>
    apiClient.knowledge.documents.delete(documentId, params),
};
