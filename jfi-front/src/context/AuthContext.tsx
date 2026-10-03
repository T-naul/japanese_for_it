'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, LoginCredentials } from '@/types';
import { authApi, authStorage } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state from storage on mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      const token = authStorage.getAccessToken();
      const cachedUser = authStorage.getUser();

      if (cachedUser) {
        setUser(cachedUser);
      }

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const currentUser = await authApi.getCurrentUser(token);
        if (isMounted) {
          setUser(currentUser);
        }
      } catch (err) {
        console.warn('Initial session validation failed, attempting refresh...', err);
        const refreshedToken = await authApi.refreshToken();
        if (refreshedToken) {
          try {
            const currentUser = await authApi.getCurrentUser(refreshedToken);
            if (isMounted) {
              setUser(currentUser);
            }
          } catch {
            if (isMounted) {
              setUser(null);
              authStorage.clear();
            }
          }
        } else {
          if (isMounted) {
            setUser(null);
            authStorage.clear();
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (credentials: LoginCredentials): Promise<User> => {
    setIsLoading(true);
    try {
      const response = await authApi.login(credentials);
      setUser(response.user);
      return response.user;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      authStorage.clear();
      setIsLoading(false);
    }
  }, []);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    try {
      const updatedUser = await authApi.getCurrentUser();
      setUser(updatedUser);
      return updatedUser;
    } catch {
      return null;
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
