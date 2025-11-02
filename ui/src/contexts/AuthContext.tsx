import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { tokenProvider } from '../utils/authState';

interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  needsLogin: boolean;
  login: (username?: string, password?: string) => Promise<void>;
  loginAnonymous: () => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [needsLogin, setNeedsLogin] = useState(false);

  const isAuthenticated = !!user && !!token;

  // Initialize auth state from token provider (not localStorage or window)
  useEffect(() => {
    const savedToken = tokenProvider.getToken();
    const savedUser = tokenProvider.getCurrentUser();
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(savedUser);
    }
    setIsLoading(false);
  }, []);

  // Update token provider when token/user changes
  useEffect(() => {
    tokenProvider.setToken(token, user);
  }, [token, user]);

  const login = async (username?: string, password?: string) => {
    try {
      setIsLoading(true);
      
      // For prototype, we always use anonymous login
      // In a real app, you'd send actual credentials
      const response = await fetch('/api/v1/auth/login-anonymous', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for cookies
        body: JSON.stringify({
          username: username || 'anonymous',
          password: password || 'anonymous'
        }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      
      setToken(data.access_token);
      setUser(data.user);
      setNeedsLogin(false);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const loginAnonymous = async () => {
    return login('anonymous', 'anonymous');
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setNeedsLogin(false);
    // Clear token provider
    tokenProvider.clearAuth();
  };

  const refreshToken = async () => {
    try {
      if (!token) {
        throw new Error('No token to refresh');
      }

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include', // Important for cookies
        body: JSON.stringify({
          refresh_token: token,
        }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      setToken(data.access_token);
      setUser(data.user);
      setNeedsLogin(false);
    } catch (error) {
      console.error('Token refresh error:', error);
      // For prototype, show login page
      // In production, this would redirect to actual login page
      setNeedsLogin(true);
      throw error;
    }
  };

  // Auto-login as anonymous on first visit (if not needing login)
  useEffect(() => {
    if (!isLoading && !isAuthenticated && !needsLogin) {
      loginAnonymous();
    }
  }, [isLoading, isAuthenticated, needsLogin]);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    needsLogin,
    login,
    loginAnonymous,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};