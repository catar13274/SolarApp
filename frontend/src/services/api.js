import axios from 'axios'

// API Configuration
// 
// In development mode (no VITE_API_URL set), use empty baseURL to leverage Vite's proxy
// In production with nginx, leave VITE_API_URL empty - nginx proxies /api to backend
// Only set VITE_API_URL for standalone deployments without nginx
//
// IMPORTANT: Do not set VITE_API_URL to hardcoded IP addresses (e.g., http://192.168.x.x)
// This will cause the app to fail when the IP changes or the server is unreachable.
// See frontend/BUILD.md for detailed configuration guide.
const API_URL = import.meta.env.VITE_API_URL || ''

// Log API configuration in development
if (import.meta.env.DEV) {
  console.log('API Configuration:', {
    baseURL: API_URL || '(using Vite proxy)',
    mode: import.meta.env.MODE,
  })
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Materials API
export const materials = {
  getAll: (params) => api.get('/api/v1/materials/', { params }),
  getById: (id) => api.get(`/api/v1/materials/${id}`),
  create: (data) => api.post('/api/v1/materials/', data),
  update: (id, data) => api.put(`/api/v1/materials/${id}`, data),
  delete: (id) => api.delete(`/api/v1/materials/${id}`),
}

// Stock API
export const stock = {
  getAll: (params) => api.get('/api/v1/stock/', { params }),
  getLowStock: () => api.get('/api/v1/stock/low'),
  getByMaterial: (materialId) => api.get(`/api/v1/stock/${materialId}`),
  getMovements: (params) => api.get('/api/v1/stock/movements/', { params }),
  createMovement: (data) => api.post('/api/v1/stock/movement', data),
}

// Projects API
export const projects = {
  getAll: (params) => api.get('/api/v1/projects/', { params }),
  getById: (id) => api.get(`/api/v1/projects/${id}`),
  create: (data) => api.post('/api/v1/projects/', data),
  update: (id, data) => api.put(`/api/v1/projects/${id}`, data),
  delete: (id) => api.delete(`/api/v1/projects/${id}`),
  addMaterial: (projectId, data) => api.post(`/api/v1/projects/${projectId}/materials`, data),
  updateMaterial: (projectId, materialId, data) => api.put(`/api/v1/projects/${projectId}/materials/${materialId}`, data),
  removeMaterial: (projectId, materialId) => api.delete(`/api/v1/projects/${projectId}/materials/${materialId}`),
  useMaterials: (projectId, data) => api.post(`/api/v1/projects/${projectId}/use-materials`, data),
  exportPDF: (projectId) => api.get(`/api/v1/projects/${projectId}/export-pdf`, { responseType: 'blob' }),
  exportWord: (projectId) => api.get(`/api/v1/projects/${projectId}/export-word`, { responseType: 'blob' }),
}

// Purchases API
export const purchases = {
  getAll: (params) => api.get('/api/v1/purchases/', { params }),
  getById: (id) => api.get(`/api/v1/purchases/${id}`),
  create: (data) => api.post('/api/v1/purchases/', data),
  updateItem: (purchaseId, itemId, data) => 
    api.put(`/api/v1/purchases/${purchaseId}/items/${itemId}`, data),
  addItemToStock: (purchaseId, itemId, materialId) => 
    api.post(`/api/v1/purchases/${purchaseId}/items/${itemId}/add-to-stock`, { material_id: materialId }),
  createMaterialFromItem: (purchaseId, itemId, data) =>
    api.post(`/api/v1/purchases/${purchaseId}/items/${itemId}/create-material`, data),
}

// Invoices API
export const invoices = {
  getAll: (params) => api.get('/api/v1/invoices/', { params }),
  getById: (id) => api.get(`/api/v1/invoices/${id}`),
  upload: (formData) => api.post('/api/v1/invoices/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  delete: (id) => api.delete(`/api/v1/invoices/${id}`),
}

// Dashboard API
export const dashboard = {
  getStats: () => api.get('/api/v1/dashboard/stats'),
}

export default api
