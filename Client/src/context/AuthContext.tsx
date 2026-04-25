import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import api from '../lib/api';
import type { UserOut } from '../types';
import { AuthContext } from './authTypes';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('ev_token')
  );
  const [loading, setLoading] = useState(!!localStorage.getItem('ev_token'));
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const fetchMe = async () => {
      try {
        const { data } = await api.get<UserOut>('/api/auth/me');
        if (!cancelled) {
          setUser(data);
          setAuthError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setToken(null);
          localStorage.removeItem('ev_token');
          setUser(null);
          // Don't set authError here for silent token expiration
          if (isAxiosError(err) && err.response?.status !== 401) {
            setAuthError('Failed to validate session. Please log in again.');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchMe();
    return () => { cancelled = true; };
  }, [token]);

  const login = async (newToken: string) => {
    try {
      localStorage.setItem('ev_token', newToken);
      setToken(newToken);
      setAuthError(null);
      const { data } = await api.get<UserOut>('/api/auth/me', {
        headers: { Authorization: `Bearer ${newToken}` },
      });
      setUser(data);
    } catch (err) {
      localStorage.removeItem('ev_token');
      setToken(null);
      setUser(null);
      
      // Handle different error response formats
      let msg = 'Login failed. Please try again.';
      
      if (isAxiosError(err)) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        if (err.response?.data) {
          const data = err.response.data;
          if (typeof data === 'object' && data !== null) {
            // Check if it's a FastAPI HTTPException format
            if ('detail' in data && typeof (data as any).detail === 'string') {
              msg = (data as any).detail;
            } 
            // Check if it's a Pydantic validation error format
            else if ('detail' in data && Array.isArray((data as any).detail)) {
              const firstError = (data as any).detail[0];
              msg =
                typeof firstError === 'object' &&
                firstError !== null &&
                'msg' in firstError &&
                typeof (firstError as { msg?: unknown }).msg === 'string'
                  ? (firstError as { msg: string }).msg
                  : 'Invalid input data.';
            } 
            // Other formats
            else {
              msg = JSON.stringify(data);
            }
          } else {
            msg = err.response ? `Error ${err.response.status}: ${err.response.statusText}` : 'An error occurred';
          }
        } else {
          msg = err.response ? `Error ${err.response.status}: ${err.response.statusText}` : 'An error occurred';
        }
      } else if (isAxiosError(err) && !err.response) {
        // The request was made but no response was received
        msg = 'Network error. Please check your connection.';
      } else {
        // Something happened in setting up the request
        msg = err instanceof Error ? err.message : 'An unexpected error occurred.';
      }
      
      setAuthError(msg);
      throw new Error(msg); // Re-throw so calling code can handle it
    }
  };

  const logout = () => {
    localStorage.removeItem('ev_token');
    setToken(null);
    setUser(null);
    setAuthError(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      authError,
      login,
      logout,
      isAuthenticated: !!user,
      isAdmin: user?.role === 'ADMIN',
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// Helper function to check if an error is an Axios error
function isAxiosError(err: unknown): err is { 
  response?: { 
    status: number; 
    statusText: string; 
    data: unknown 
  }; 
  request?: unknown 
} {
  return (
    typeof err === 'object' &&
    err !== null &&
    'response' in err &&
    typeof (err as any).response === 'object'
  );
}