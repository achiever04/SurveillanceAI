import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  // FIXED: Removed the hardcoded 'Content-Type' header here.
  // Axios will automatically set the correct type (JSON vs Form Data) based on the payload.
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API endpoints
export const authAPI = {
  // Ensure we can pass config overrides if needed
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
};

export const cameraAPI = {
  getAll: () => api.get('/cameras'),
  getById: (id) => api.get(`/cameras/${id}`),
  create: (data) => api.post('/cameras', data),
  update: (id, data) => api.put(`/cameras/${id}`, data),
  delete: (id) => api.delete(`/cameras/${id}`),
  getStream: (id) => `${API_BASE_URL}/cameras/${id}/stream`,
};

export const detectionAPI = {
  getAll: (params) => api.get('/detections', { params }),
  getById: (id) => api.get(`/detections/${id}`),
  updateStatus: (id, status) => api.patch(`/detections/${id}/status`, { status }),
};

export const watchlistAPI = {
  getAll: () => api.get('/watchlist'),
  getById: (id) => api.get(`/watchlist/${id}`),
  // FIXED: Explicitly allow FormData for file uploads
  create: (formData) => api.post('/watchlist', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  update: (id, data) => api.put(`/watchlist/${id}`, data),
  delete: (id) => api.delete(`/watchlist/${id}`),
};

export const blockchainAPI = {
  getEvidence: (eventId) => api.get(`/blockchain/evidence/${eventId}`),
  verifyIntegrity: (eventId) => api.post(`/blockchain/verify/${eventId}`),
  getTransactions: (params) => api.get('/blockchain/transactions', { params }),
};

export const analyticsAPI = {
  getDashboardStats: () => api.get('/analytics/dashboard'),
  getDetectionTrends: (params) => api.get('/analytics/trends', { params }),
  getCameraHealth: () => api.get('/analytics/camera-health'),
};

export default api;