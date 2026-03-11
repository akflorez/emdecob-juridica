export type UserRole = 'admin' | 'user';

export interface User {
  id: number;
  username: string;
  nombre: string;
  is_admin: boolean;
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Permisos por rol
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: ['importar', 'consultar', 'casos', 'usuarios', 'configuracion'],
  user:  ['consultar', 'casos'],
};

export function hasPermission(user: User | null, permission: string): boolean {
  if (!user) return false;
  const role = user.is_admin ? 'admin' : 'user';
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}