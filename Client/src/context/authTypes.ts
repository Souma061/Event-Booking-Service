import { createContext } from 'react';
import type { UserOut } from '../types';

export interface AuthContextType {
  user: UserOut | null;
  loading: boolean;
  authError: string | null;
  /** Used by regular email/password login — sends credentials, backend sets cookie */
  login: (email: string, password: string) => Promise<void>;
  /** Fetches /api/auth/me using the existing HTTP-only cookie (used post-OAuth redirect) */
  fetchUser: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);