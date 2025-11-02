/**
 * Central authentication state management
 * 
 * This module maintains JWT tokens in module scope only,
 * preventing XSS attacks through global window access.
 */

// Private module-scoped variables (not accessible globally)
let currentToken: string | null = null;
let currentUser: any = null;

// Interface for AuthContext to get token
export interface TokenProvider {
  getToken(): string | null;
  setToken(token: string | null, user: any): void;
  getCurrentUser(): any;
  clearAuth(): void;
}

// Create token provider for secure access
export const createTokenProvider = (): TokenProvider => ({
  getToken() {
    return currentToken;
  },
  
  setToken(token: string | null, user: any) {
    currentToken = token;
    currentUser = user;
  },
  
  getCurrentUser() {
    return currentUser;
  },
  
  clearAuth() {
    currentToken = null;
    currentUser = null;
  }
});

// Export the token provider instance
export const tokenProvider = createTokenProvider();