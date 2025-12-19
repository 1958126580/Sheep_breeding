import apiClient from './client';

export interface Farm {
  id?: number;
  code: string;
  name: string;
  farm_type: string;
  capacity: number;
  address?: string;
  contact_person?: string;
  contact_phone?: string;
}

export const farmAPI = {
  list: (params?: any) => apiClient.get('/api/v1/farms', { params }),
  get: (id: number) => apiClient.get(`/api/v1/farms/${id}`),
  create: (data: Farm) => apiClient.post('/api/v1/farms', data),
  update: (id: number, data: Farm) => apiClient.put(`/api/v1/farms/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/v1/farms/${id}`),
};

export const breedingValueAPI = {
  listRuns: (params?: any) => apiClient.get('/api/v1/breeding-values/runs', { params }),
  createRun: (data: any) => apiClient.post('/api/v1/breeding-values/runs', data),
  getResults: (runId: number) => apiClient.get(`/api/v1/breeding-values/runs/${runId}/results`),
};

export const systemAPI = {
  getInfo: () => apiClient.get('/api/v1/info'),
  healthCheck: () => apiClient.get('/health'),
};
