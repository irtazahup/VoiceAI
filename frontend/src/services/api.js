import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  register: (userData) => api.post('/register', userData),
  login: (credentials) => api.post('/login', credentials),
  getCurrentUser: () => api.get('/me'),
};

// Recording APIs
export const recordingAPI = {
  upload: (formData) => {
    return api.post('/upload-recording/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  getAll: () => api.get('/recordings/'),
  
  getById: (id) => api.get(`/recordings/${id}`),
  
  delete: (id) => api.delete(`/recordings/${id}`),
  
  processNow: (id) => api.post(`/recordings/${id}/process-now`),
  
  process: (id) => api.post(`/recordings/${id}/process`),
  
  getStatus: (id) => api.get(`/recordings/${id}/status`),
  
  getSummary: (id) => api.get(`/recordings/${id}/summary`),
};

// Summary APIs
export const summaryAPI = {
  getAll: () => api.get('/summaries/'),
};

// Streaming API for real-time processing updates
export class StreamingAPI {
  static createEventSource(recordingId, onMessage, onError) {
    // For now, we'll use polling since FastAPI streaming would need SSE implementation
    let pollInterval;
    
    const poll = async () => {
      try {
        const response = await recordingAPI.getStatus(recordingId);
        onMessage(response.data);
        
        if (response.data.status === 'completed' || response.data.status === 'error') {
          clearInterval(pollInterval);
        }
      } catch (error) {
        onError(error);
        clearInterval(pollInterval);
      }
    };
    
    // Start polling every 2 seconds
    pollInterval = setInterval(poll, 2000);
    
    // Return cleanup function
    return () => clearInterval(pollInterval);
  }
}

export default api;
