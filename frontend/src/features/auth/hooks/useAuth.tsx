import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { httpClient } from '../../../lib/http/client';
import { UserCreate, UserLogin, UserProfile } from '../../../types';
import { authApi } from '../api/authApi';

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  error?: string;
}

interface AuthContextValue extends AuthState {
  login: (payload: UserLogin) => Promise<void>;
  register: (payload: UserCreate) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AUTH_STORAGE_KEY = 'fhe-auth-state';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredAuth(): Pick<AuthState, 'user' | 'token'> {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) return { user: null, token: null };
  try {
    return JSON.parse(raw) as { user: UserProfile | null; token: string | null };
  } catch (err) {
    console.warn('Failed to parse stored auth state', err);
    return { user: null, token: null };
  }
}

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const stored = readStoredAuth();
  const [user, setUser] = useState<UserProfile | null>(stored.user);
  const [token, setToken] = useState<string | null>(stored.token);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  useEffect(() => {
    httpClient.setToken(token);
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ user, token }));
  }, [token, user]);

  const login = async (payload: UserLogin) => {
    setLoading(true);
    setError(undefined);
    try {
      const res = await authApi.login(payload);
      setToken(res.access_token);
      setUser({ user_id: payload.user_id });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (payload: UserCreate) => {
    setLoading(true);
    setError(undefined);
    try {
      const profile = await authApi.register(payload);
      setUser(profile);
      // auto-login not implemented; user should log in separately
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    httpClient.setToken(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, loading, error, login, register, logout, isAuthenticated: Boolean(token) }),
    [user, token, loading, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
