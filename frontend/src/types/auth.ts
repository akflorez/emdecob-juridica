export type UserRole = 'admin' | 'user';

export interface User {
  id: number;
  username: string;
  nombre: string;
  email?: string;
  is_admin: boolean;
  is_superadmin?: boolean;  // Alias para is_admin en contexto global
  is_active: boolean;
  company_id?: number | null;
  roles?: string[];
  permissions?: string[];
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
  admin: ['importar', 'consultar', 'casos', 'usuarios', 'configuracion', 'superadmin'],
  user:  ['consultar', 'casos'],
};

export function hasPermission(user: User | null, permission: string): boolean {
  if (!user) return false;
  const role = user.is_admin ? 'admin' : 'user';
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

/** Verifica si el usuario es Superadmin global */
export function isSuperAdmin(user: User | null): boolean {
  if (!user) return false;
  // Superadmin = is_superadmin explícito, O is_admin=true (sin importar company_id)
  return !!(user.is_superadmin || user.is_admin);
}