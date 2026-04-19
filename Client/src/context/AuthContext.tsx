import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../lib/api';
import type { UserOut } from '../types';

interface AuthContextType {
  user: UserOut | null;
  token: string | null;
  loading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('ev_token')
  );
  const [loading, setLoading] = useState(!!localStorage.getItem('ev_token'));

  const fetchMe = async () => {
    try {
      const { data } = await api.get<UserOut>('/api/auth/me');
      setUser(data);
    } catch {
      setToken(null);
      localStorage.removeItem('ev_token');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchMe();
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

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
