import axios from 'axios'

// In development mode (no VITE_API_URL set), use empty baseURL to leverage Vite's proxy
// In production, VITE_API_URL should be set to the actual backend URL
const API_URL = import.meta.env.VITE_API_URL || ''

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
}

// Purchases API
export const purchases = {
  getAll: (params) => api.get('/api/v1/purchases/', { params }),
  getById: (id) => api.get(`/api/v1/purchases/${id}`),
  create: (data) => api.post('/api/v1/purchases/', data),
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
}

// Dashboard API
export const dashboard = {
  getStats: () => api.get('/api/v1/dashboard/stats'),
}

export default api
