import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, AuthState, LoginCredentials } from '@/types/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_STORAGE_KEY = 'emdecob_auth_token';
const AUTH_USER_KEY    = 'emdecob_auth_user';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string || 'http://localhost:8000').replace(/\/$/, '');

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Al iniciar, restaurar sesión guardada y verificar con el backend
  useEffect(() => {
    const token = localStorage.getItem(AUTH_STORAGE_KEY);
    const savedUser = localStorage.getItem(AUTH_USER_KEY);

    if (!token || !savedUser) {
      setState({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    // Verificar que el token sigue siendo válido
    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Token inválido');
        return res.json();
      })
      .then((user: User) => {
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        setState({ user, isAuthenticated: true, isLoading: false });
      })
      .catch(() => {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        localStorage.removeItem(AUTH_USER_KEY);
        setState({ user: null, isAuthenticated: false, isLoading: false });
      });
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setState(prev => ({ ...prev, isLoading: false }));
        return { success: false, error: data?.detail || 'Usuario o contraseña incorrectos' };
      }

      const data = await res.json();
      const { token, user } = data;

      localStorage.setItem(AUTH_STORAGE_KEY, token);
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));

      setState({ user, isAuthenticated: true, isLoading: false });
      return { success: true };

    } catch (e) {
      setState(prev => ({ ...prev, isLoading: false }));
      return { success: false, error: 'No se pudo conectar al servidor' };
    }
  }, []);

  const logout = useCallback(() => {
    const token = localStorage.getItem(AUTH_STORAGE_KEY);
    if (token) {
      fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
}

// Helper para hacer fetch autenticado desde cualquier parte
export function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_STORAGE_KEY);
}
