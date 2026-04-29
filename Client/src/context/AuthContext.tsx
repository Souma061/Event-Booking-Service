import { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import axios from 'axios';
import api from '../lib/api';
import type { UserOut } from '../types';
import { AuthContext } from './authTypes';

type FastApiValidationError = {
  msg?: unknown;
};

type FastApiErrorResponse = {
  detail?: string | FastApiValidationError[];
};

function extractErrorMessage(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err)) {
    return err instanceof Error ? err.message : fallback;
  }
  if (!err.response) return 'Network error. Please check your connection.';
  const data = err.response.data as FastApiErrorResponse | undefined;
  if (!data) return `Error ${err.response.status}: ${err.response.statusText}`;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    const first = data.detail[0];
    return typeof first === 'object' && first !== null && typeof (first as { msg?: unknown }).msg === 'string'
      ? (first as { msg: string }).msg
      : 'Invalid input data.';
  }
  return JSON.stringify(data);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  /**
   * Hit /api/auth/me using the existing HTTP-only cookie.
   * This is the single source of truth for auth state.
   */
  const fetchUser = useCallback(async () => {
    try {
      const { data } = await api.get<UserOut>('/api/auth/me');
      setUser(data);
      setAuthError(null);
    } catch (err) {
      setUser(null);
      if (axios.isAxiosError(err) && err.response?.status !== 401) {
        setAuthError('Failed to validate session. Please log in again.');
      }
      // Re-throw so callers (e.g. OAuthCallback) can catch failures
      throw err;
    }
  }, []);

  // On mount, silently check whether a valid session cookie already exists
  // (covers page refresh, existing cookie from a previous session).
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const { data } = await api.get<UserOut>('/api/auth/me');
        if (!cancelled) {
          setUser(data);
          setAuthError(null);
        }
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    check();
    return () => { cancelled = true; };
  }, []);

  /**
   * Email/password login.
   * The backend sets the HTTP-only cookie and returns the Userout object.
   */
  const login = useCallback(async (email: string, password: string) => {
    try {
      const { data } = await api.post<UserOut>('/api/auth/login', { email, password });
      setUser(data);
      setAuthError(null);
    } catch (err) {
      setUser(null);
      const msg = extractErrorMessage(err, 'Login failed. Please try again.');
      setAuthError(msg);
      throw new Error(msg);
    }
  }, []);

  /**
   * Clears the HTTP-only cookie via the logout endpoint, then clears local state.
   */
  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // Even if the server call fails, clear local state so the UI reflects logged-out
    }
    setUser(null);
    setAuthError(null);
  }, []);

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      authError,
      login,
      fetchUser,
      logout,
      isAuthenticated: !!user,
      isAdmin: user?.role === 'ADMIN',
    }}>
      {children}
    </AuthContext.Provider>
  );
}
