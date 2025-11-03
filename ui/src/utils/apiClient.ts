type User = any // TODO

class ApiClient {
  private baseUrl: string;
  private currentToken: string | null = null;
  private currentUser: User = null;

  constructor() {
    // Use relative path - Vite automatically proxies /api to backend in development
    // In production, this works as relative path to same domain
    this.baseUrl = '/api/v1';
  }

  private getToken(): string | null {
    // Get token from memory
    return this.currentToken;
  }

  private setToken(token: string, user: User) {
    this.currentToken = token;
    this.currentUser = user;
  }

  private async request(
    endpoint: string,
    options: RequestInit = {},
    extraOptions?: { isRefresh?: boolean }
  ): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    // Add authentication header if token exists
    const headers: Record<string, string> = {};

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Set Content-Type to JSON only for non-FormData requests
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    // Merge with any additional headers
    Object.assign(headers, options.headers);

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized - try to refresh token (unless this is already a refresh request)
    if (response.status === 401 && !extraOptions?.isRefresh) {
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
        // Refresh failed - try anonymous login as fallback
        await this.login("anonymous", "anonymous");
        // Retry with anonymous token
        const anonToken = this.getToken();
        const anonHeaders = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${anonToken}`,
          ...options.headers,
        };

        return fetch(url, {
          ...options,
          headers: anonHeaders,
        });
      }
    }

    return response;
  }

  private async refreshToken(): Promise<void> {
    const response = await this.request('/auth/refresh', {
      method: 'POST',
      credentials: 'include', // Important for HttpOnly cookies
    }, { isRefresh: true });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    this.setToken(data.access_token, data.user);
  }

  // Authentication endpoints
  async login(username: string, password: string): Promise<any> {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    this.setToken(data.access_token, data.user);
    return data.user;
  }  


  getCurrentUser(): any {
    return this.currentUser;
  }

  isAuthenticated(): boolean {
    return !!this.currentToken && !!this.currentUser;
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

  async uploadProjectFiles(projectId: number, files: File[], metadata?: string | null) {
    const formData = new FormData();

    files.forEach((file) => {
      formData.append('files', file);
    });

    if (metadata) {
      formData.append('metadata', metadata);
    }

    const response = await this.request(`/projects/${projectId}/upload`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header, let browser set it with boundary for FormData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload files');
    }

    return response.json();
  }

  async getProjectSources(projectId: number) {
    const response = await this.request(`/projects/${projectId}/sources`);

    if (!response.ok) {
      throw new Error('Failed to get project sources');
    }

    return response.json();
  }

  async deleteProjectSource(projectId: number, sourceId: number) {
    const response = await this.request(`/projects/${projectId}/sources/${sourceId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete source');
    }

    return response.json();
  }

  // Node management endpoints
  async deleteNode(nodeId: string, projectId?: string) {
    const url = projectId
      ? `/nodes/${encodeURIComponent(nodeId)}?project_id=${encodeURIComponent(projectId)}`
      : `/nodes/${encodeURIComponent(nodeId)}`;

    const response = await this.request(url, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete node');
    }

    return response.json();
  }

  async updateNodeMetadata(nodeId: string, metadata: any, projectId?: string) {
    // Check if this is a source node
    if (nodeId.startsWith('source-') && projectId) {
      const sourceId = parseInt(nodeId.replace('source-', ''));
      const response = await this.request(`/projects/${projectId}/sources/${sourceId}/metadata`, {
        method: 'PUT',
        body: JSON.stringify(metadata),
      });

      if (!response.ok) {
        throw new Error('Failed to update source metadata');
      }

      return response.json();
    } else {
      // Regular node metadata update
      const url = projectId
        ? `/nodes/${encodeURIComponent(nodeId)}/metadata?project_id=${encodeURIComponent(projectId)}`
        : `/nodes/${encodeURIComponent(nodeId)}/metadata`;

      const response = await this.request(url, {
        method: 'PUT',
        body: JSON.stringify({
          node_id: nodeId,
          metadata: metadata,
          project_id: projectId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update node metadata');
      }

      return response.json();
    }
  }

  // Public methods for AuthContext
  async initialize(): Promise<{ user: User; isAuthenticated: boolean }> {
    try {
      // Try to refresh using existing cookie
      await this.refreshToken();
      return {
        user: this.currentUser,
        isAuthenticated: true
      };
    } catch (refreshError) {
      // No valid refresh token, try anonymous login
      // TODO: After prototype we redirect to login page
      try {
        await this.login("anonymous", "anonymous");
        return {
          user: this.currentUser,
          isAuthenticated: true
        };
      } catch (anonError) {
        // Both failed - no authentication
        return {
          user: null,
          isAuthenticated: false
        };
      }
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export hook for easy usage in components
export const useApiClient = () => {
  return apiClient;
};