import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { tokenProvider } from '../utils/authState';
import { apiClient } from '../utils/apiClient';

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
  const hasAttemptedAutoLogin = useRef(false);

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

  const login = useCallback(async (username?: string, password?: string) => {
    try {
      setIsLoading(true);
      
      // Use apiClient which handles baseUrl and authentication
      const data = await apiClient.login(username || 'anonymous', password || 'anonymous');
      
      setToken(data.access_token);
      setUser(data.user);
      setNeedsLogin(false);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setNeedsLogin(false);
    hasAttemptedAutoLogin.current = false; // Reset auto-login flag on logout
    // Clear token provider
    tokenProvider.clearAuth();
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      if (!token) {
        throw new Error('No token to refresh');
      }

      // Use apiClient's built-in token refresh mechanism
      // The apiClient will automatically handle token refresh on 401 errors
      // For manual refresh, we can trigger a validation request
      const data = await apiClient.validateToken();
      
      // Update user data if validation succeeds
      if (data.user) {
        setUser(data.user);
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      // For prototype, show login page
      // In production, this would redirect to actual login page
      setNeedsLogin(true);
      throw error;
    }
  }, [token]);

  // Auto-login as anonymous on first visit (if not needing login)
  useEffect(() => {
    if (!isLoading && !isAuthenticated && !needsLogin && !hasAttemptedAutoLogin.current) {
      hasAttemptedAutoLogin.current = true;
      login();
    }
  }, [isLoading, isAuthenticated, needsLogin, login]);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    needsLogin,
    login,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
