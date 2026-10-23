import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
};

export const chatAPI = {
  send: (message, sessionId) => api.post('/chat', { message, session_id: sessionId }),
  history: () => api.get('/chat/history'),
  messages: (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`),
  clearSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
};

export const documentsAPI = {
  list: () => api.get('/documents'),
  upload: (formData) => api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete: (id) => api.delete(`/documents/${id}`),
  reindex: (id) => api.post(`/documents/${id}/reindex`),
};

export const ticketsAPI = {
  list: () => api.get('/tickets'),
  create: (data) => api.post('/tickets', data),
};

export const adminAPI = {
  analytics: () => api.get('/admin/analytics'),
};

export const feedbackAPI = {
  submit: (data) => api.post('/feedback', data),
};

export default api;
