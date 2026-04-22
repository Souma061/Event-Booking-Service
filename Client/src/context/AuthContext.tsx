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

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const fetchMe = async () => {
      try {
        const { data } = await api.get<UserOut>('/api/auth/me');
        if (!cancelled) setUser(data);
      } catch {
        if (!cancelled) {
          setToken(null);
          localStorage.removeItem('ev_token');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchMe();
    return () => { cancelled = true; };
  }, [token]);

  const login = async (newToken: string) => {
    localStorage.setItem('ev_token', newToken);
    setToken(newToken);
    const { data } = await api.get<UserOut>('/api/auth/me', {
      headers: { Authorization: `Bearer ${newToken}` },
    });
    setUser(data);
  };

  const logout = () => {
    localStorage.removeItem('ev_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      logout,
      isAuthenticated: !!user,
      isAdmin: user?.role === 'ADMIN',
    }}>
      {children}
    </AuthContext.Provider>
  );
}
