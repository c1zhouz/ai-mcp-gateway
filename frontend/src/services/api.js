import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Dashboard
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getTrend: () => api.get('/dashboard/trend'),
  getTopTools: () => api.get('/dashboard/top-tools'),
  getActivities: () => api.get('/dashboard/activities'),
  getAlerts: () => api.get('/dashboard/alerts'),
};

// Gateway
export const gatewayAPI = {
  getConfig: () => api.get('/gateway/config'),
  updateConfig: (data) => api.put('/gateway/config', data),
  getApiKeys: () => api.get('/gateway/api-keys'),
  createApiKey: (data) => api.post('/gateway/api-keys', data),
  deleteApiKey: (id) => api.delete(`/gateway/api-keys/${id}`),
  getRoutes: () => api.get('/gateway/routes'),
  createRoute: (data) => api.post('/gateway/routes', data),
  updateRoute: (id, data) => api.put(`/gateway/routes/${id}`, data),
  deleteRoute: (id) => api.delete(`/gateway/routes/${id}`),
};

// Services
export const servicesAPI = {
  list: () => api.get('/services'),
  get: (id) => api.get(`/services/${id}`),
  create: (data) => api.post('/services', data),
  update: (id, data) => api.put(`/services/${id}`, data),
  delete: (id) => api.delete(`/services/${id}`),
  getTools: (id) => api.get(`/services/${id}/tools`),
  healthCheck: (id) => api.post(`/services/${id}/health-check`),
  syncTools: (id) => api.post(`/services/${id}/sync-tools`),
};

// Tools
export const toolsAPI = {
  list: (params) => api.get('/tools', { params }),
  get: (id) => api.get(`/tools/${id}`),
  create: (data) => api.post('/tools', data),
  update: (id, data) => api.put(`/tools/${id}`, data),
  updateStatus: (id, enabled) => api.patch(`/tools/${id}`, { enabled }),
  delete: (id) => api.delete(`/tools/${id}`),
  deploy: (id) => api.post(`/tools/${id}/deploy`),
};

// Chat
export const chatAPI = {
  getSessions: () => api.get('/chat/sessions'),
  getMessages: (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`),
  deleteSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
};

export default api;
