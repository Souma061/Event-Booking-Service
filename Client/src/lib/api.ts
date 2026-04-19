import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

/* ─── Attach JWT from localStorage ─── */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ev_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ─── Global 401 handler ─── */
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ev_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;
