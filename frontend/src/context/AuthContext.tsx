import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { User } from '../types/auth';
import { authApi } from '../api/authApi';
import {
  getRefreshToken,
  setAccessToken,
  setRefreshToken,
  setOnUnauthorizedCallback,
} from '../api/client';
import axios from 'axios';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  // Restore session on app load via Refresh Token
  useEffect(() => {
    const initAuth = async () => {
      const storedRefreshToken = getRefreshToken();
      if (!storedRefreshToken) {
        setIsLoading(false);
        return;
      }

      try {
        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';
        const refreshResp = await axios.post(`${apiBaseUrl}/auth/refresh`, {
          refresh_token: storedRefreshToken,
        });

        const { access_token, refresh_token: newRefreshToken } = refreshResp.data;
        setAccessToken(access_token);
        setRefreshToken(newRefreshToken);

        const userData = await authApi.getMe();
        setUser(userData);
      } catch {
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    setOnUnauthorizedCallback(() => {
      setUser(null);
      setAccessToken(null);
      setRefreshToken(null);
    });

    initAuth();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const tokens = await authApi.login(username, password);
      setAccessToken(tokens.access_token);
      setRefreshToken(tokens.refresh_token);

      const userData = await authApi.getMe();
      setUser(userData);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || 'Erro ao realizar login. Verifique suas credenciais.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    setError(null);
    setIsLoading(true);
    try {
      await authApi.register(email, password, fullName);
      // Automatically login after successful registration
      await login(email, password);
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || 'Erro ao cadastrar conta. Tente novamente.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  const logout = useCallback(async () => {
    const token = getRefreshToken();
    if (token) {
      try {
        await authApi.logout(token);
      } catch {
        // Continue clean up even if network error
      }
    }
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
  }, []);

  const contextValue = useMemo<AuthContextType>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout,
      error,
      clearError,
    }),
    [user, isLoading, login, register, logout, error, clearError]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser utilizado dentro de um AuthProvider');
  }
  return context;
};
