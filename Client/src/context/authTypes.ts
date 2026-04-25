import { createContext } from 'react';
import type { UserOut } from '../types';

export interface AuthContextType {
  user: UserOut | null;
  token: string | null;
  loading: boolean;
  authError: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);