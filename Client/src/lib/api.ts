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
    // Only redirect to login for 401 errors that aren't already on login/register pages
    if (err.response?.status === 401) {
      const currentPath = window.location.pathname;
      const isAuthPage = currentPath.includes('/login') || 
                        currentPath.includes('/register') ||
                        currentPath.includes('/admin/login');
      
      if (!isAuthPage) {
        localStorage.removeItem('ev_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;