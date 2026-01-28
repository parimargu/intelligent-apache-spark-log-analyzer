import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// API functions
export const logApi = {
    list: (params) => api.get('/logs', { params }),
    get: (id) => api.get(`/logs/${id}`),
    getEntries: (id, params) => api.get(`/logs/${id}/entries`, { params }),
    delete: (id) => api.delete(`/logs/${id}`)
}

export const ingestionApi = {
    upload: (file, onProgress) => {
        const formData = new FormData()
        formData.append('file', file)

        return api.post('/ingestion/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total))
        })
    },
    uploadBatch: (files, onProgress) => {
        const formData = new FormData()
        files.forEach((file) => formData.append('files', file))

        return api.post('/ingestion/upload/batch', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / e.total))
        })
    }
}

export const analysisApi = {
    list: (params) => api.get('/analysis', { params }),
    get: (id) => api.get(`/analysis/${id}`),
    create: (data) => api.post('/analysis', data),
    delete: (id) => api.delete(`/analysis/${id}`)
}

export const reportApi = {
    dashboard: () => api.get('/reports/dashboard'),
    list: (params) => api.get('/reports', { params }),
    get: (id) => api.get(`/reports/${id}`),
    create: (data) => api.post('/reports', data),
    delete: (id) => api.delete(`/reports/${id}`)
}

export default api
