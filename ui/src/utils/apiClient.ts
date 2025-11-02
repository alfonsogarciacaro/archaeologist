import { tokenProvider } from './authState';

class ApiClient {
  private baseUrl: string;

  constructor() {
    // Use relative path - Vite automatically proxies /api to backend in development
    // In production, this works as relative path to same domain
    this.baseUrl = '/api/v1';
  }

  private getToken(): string | null {
    // Get token from secure module-scoped provider (not window object)
    return tokenProvider.getToken();
  }

  private async request(
    endpoint: string,
    options: RequestInit = {},
    extraOptions?: { isRefresh?: boolean }
  ): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    // Add authentication header if token exists
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized - try to refresh token (unless this is already a refresh request)
    if (response.status === 401 && token && !extraOptions?.isRefresh) {
      try {
        await this.refreshToken();
        // Retry original request with new token
        const newToken = this.getToken();
        const newHeaders = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newToken}`,
          ...options.headers,
        };

        return fetch(url, {
          ...options,
          headers: newHeaders,
        });
      } catch (refreshError) {
        // Refresh failed - will be handled by AuthContext
        // For prototype, this triggers automatic re-login as anonymous
        throw refreshError;
      }
    }

    return response;
  }

  private async refreshToken(): Promise<void> {
    const token = this.getToken();
    if (!token) {
      throw new Error('No token to refresh');
    }

    const response = await this.request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({
        refresh_token: token,
      }),
      credentials: 'include', // Important for cookies
    }, { isRefresh: true }); // Prevent infinite refresh loop

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    
    // Update token through AuthContext (not localStorage)
    const authState = (window as any).__ARCHAEOLOGIST_AUTH_STATE__;
    if (authState?.setAuthState) {
      authState.setAuthState(data.access_token, data.user);
    }
  }

  // Authentication endpoints
  async login(username: string, password: string) {
    const response = await this.request('/auth/login-anonymous', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
      credentials: 'include', // Important for cookies
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    return response.json();
  }

  async getCurrentUser() {
    const response = await this.request('/auth/me');
    
    if (!response.ok) {
      throw new Error('Failed to get current user');
    }

    return response.json();
  }

  async validateToken() {
    const response = await this.request('/auth/validate-token');
    
    if (!response.ok) {
      throw new Error('Token validation failed');
    }

    return response.json();
  }

  // Investigation endpoints
  async investigate(query: string) {
    const response = await this.request('/investigate', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      throw new Error('Investigation failed');
    }

    return response.json();
  }

  async getInvestigationStatus() {
    const response = await this.request('/investigation-status');
    
    if (!response.ok) {
      throw new Error('Failed to get investigation status');
    }

    return response.json();
  }

  // Project endpoints
  async getProjects() {
    const response = await this.request('/projects');
    
    if (!response.ok) {
      throw new Error('Failed to get projects');
    }

    return response.json();
  }

  async getProject(projectId: number) {
    const response = await this.request(`/projects/${projectId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get project');
    }

    return response.json();
  }

  async createProject(projectData: any) {
    const response = await this.request('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });

    if (!response.ok) {
      throw new Error('Failed to create project');
    }

    return response.json();
  }

  async updateProject(projectId: number, projectData: any) {
    const response = await this.request(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });

    if (!response.ok) {
      throw new Error('Failed to update project');
    }

    return response.json();
  }

  async deleteProject(projectId: number) {
    const response = await this.request(`/projects/${projectId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete project');
    }

    return response.json();
  }

  async getProjectUsers(projectId: number) {
    const response = await this.request(`/projects/${projectId}/users`);
    
    if (!response.ok) {
      throw new Error('Failed to get project users');
    }

    return response.json();
  }

  async addProjectUser(projectId: number, userData: any) {
    const response = await this.request(`/projects/${projectId}/users`, {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error('Failed to add user to project');
    }

    return response.json();
  }

  async updateProjectUserRole(projectId: number, userId: number, role: string) {
    const response = await this.request(`/projects/${projectId}/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });

    if (!response.ok) {
      throw new Error('Failed to update user role');
    }

    return response.json();
  }

  async removeProjectUser(projectId: number, userId: number) {
    const response = await this.request(`/projects/${projectId}/users/${userId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to remove user from project');
    }

    return response.json();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export hook for easy usage in components
export const useApiClient = () => {
  return apiClient;
};