import axios from 'axios';

// VITE_API_URL points to the backend (default: http://localhost:8000).
// withCredentials: true ensures the HTTP-only auth cookie is sent on every request.
// In dev, localhost cookies are shared across ports so cross-origin requests work fine
// with CORS allow_credentials=True on the backend.
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
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
        // We don't need to remove ev_token from localStorage anymore as we use cookies,
        // but we might want to clear any cached user state in AuthContext
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;