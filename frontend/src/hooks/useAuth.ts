'use client';

import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/constants';

export function useAuth() {
  const { user, isAuthenticated, isLoading, error, login, register, logout, clearError, setUser } =
    useAuthStore();
  const router = useRouter();

  const handleLogin = async (email: string, password: string) => {
    await login(email, password);
    router.push(ROUTES.dashboard);
  };

  const handleRegister = async (
    email: string,
    password: string,
    name: string,
    whatsapp_number?: string,
  ) => {
    await register(email, password, name, whatsapp_number);
    router.push(ROUTES.dashboard);
  };

  const handleLogout = () => {
    logout();
    router.push(ROUTES.login);
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    clearError,
    setUser,
    isAdmin: user?.role === 'admin',
    isOperator: user?.role === 'operator' || user?.role === 'admin',
  };
}
