import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const imageApi = {
  upload: (files) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    return api.post('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  scanDirectory: (directoryPath) => api.post('/images/scan-directory', null, {
    params: { directory_path: directoryPath }
  }),
  list: (params) => api.get('/images', { params }),
  search: (keyword) => api.get('/images', { params: { search: keyword } }),
  get: (id) => api.get(`/images/${id}`),
  getFile: (id) => `${API_BASE}/images/${id}/file`,
  delete: (id) => api.delete(`/images/${id}`),
  correct: (id, detections) => api.post(`/images/${id}/correct`, { detections })
}

export const labelingApi = {
  start: (data) => api.post('/labeling/start', data),
  list: () => api.get('/labeling/tasks'),
  get: (id) => api.get(`/labeling/tasks/${id}`)
}

export const datasetApi = {
  build: (data) => api.post('/dataset/build', data),
  list: () => api.get('/datasets'),
  get: (id) => api.get(`/datasets/${id}`)
}

export const trainingApi = {
  start: (data) => api.post('/training/start', data),
  list: () => api.get('/training/tasks'),
  get: (id) => api.get(`/training/tasks/${id}`),
  stop: (id) => api.post(`/training/tasks/${id}/stop`)
}

export const modelApi = {
  list: () => api.get('/models'),
  get: (id) => api.get(`/models/${id}`),
  export: (id, format) => api.post(`/models/${id}/export`, { format }),
  download: (id, format = 'pt') => `${API_BASE}/models/${id}/download?format=${format}`,
  delete: (id) => api.delete(`/models/${id}`)
}

export const healthApi = {
  check: () => api.get('/health')
}

export const pipelineApi = {
  start: (data) => api.post('/pipeline/start', data),
  getStatus: () => api.get('/pipeline/status'),
  getTrainingProgress: () => api.get('/pipeline/training-progress'),
  stop: () => api.post('/pipeline/stop')
}

export default api
