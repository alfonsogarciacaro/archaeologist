# Authentication & Project Management Implementation

## Overview

This document describes the complete authentication and project management system implemented for the Enterprise Code Archaeologist prototype. The system provides JWT-based authentication with anonymous access for the prototype, and a full project management framework with role-based access control.

## Features Implemented

### 1. Authentication System

#### Backend (FastAPI)
- **JWT Token Management**: Complete JWT token creation, verification, and refresh functionality
- **Anonymous Access**: Prototype automatically authenticates users as "anonymous" for testing
- **Authentication Routes**: 
  - `POST /api/v1/auth/login-anonymous` - Get anonymous token
  - `POST /api/v1/auth/login` - Standard login (prototype: always returns anonymous)
  - `POST /api/v1/auth/refresh` - Refresh JWT token
  - `GET /api/v1/auth/me` - Get current user info
  - `GET /api/v1/auth/validate-token` - Validate JWT token
  - `POST /api/v1/auth/logout` - Logout user
- **Dependencies**: 
  - `get_current_user` - Requires valid JWT token
  - `get_current_admin_user` - Requires admin user
  - `get_optional_user` - Optional authentication
  - `get_current_user_or_anonymous` - Auto-anonymous fallback

#### Frontend (React)
- **Authentication Context**: Global auth state management with React Context
- **Auto-login**: Automatically authenticates as anonymous on first visit
- **Token Storage**: Secure localStorage token management
- **API Client**: Integrated JWT handling with automatic token refresh
- **Loading States**: Proper loading screens during auth initialization

### 2. Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### Projects Table
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    repository_paths TEXT,  -- JSON array
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

#### Project Users Table (Many-to-Many)
```sql
CREATE TABLE project_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### Updated Investigations Table
- Added `project_id` foreign key for project association
- All investigations can now be linked to specific projects

### 3. Project Management API

#### Core Project Operations
- **Create Projects**: `POST /api/v1/projects`
- **Get User Projects**: `GET /api/v1/projects`
- **Get Single Project**: `GET /api/v1/projects/{id}`
- **Update Project**: `PUT /api/v1/projects/{id}`
- **Delete Project**: `DELETE /api/v1/projects/{id}`

#### User Management in Projects
- **Get Project Users**: `GET /api/v1/projects/{id}/users`
- **Add User to Project**: `POST /api/v1/projects/{id}/users`
- **Update User Role**: `PUT /api/v1/projects/{id}/users/{user_id}`
- **Remove User from Project**: `DELETE /api/v1/projects/{id}/users/{user_id}`

#### Role-Based Access Control
- **Owner**: Full project control, can manage users
- **Admin**: Can manage project content and users
- **Member**: Can create investigations and view project data
- **Viewer**: Read-only access to project data

### 4. Authentication Flow

#### Prototype Anonymous Flow
1. User visits application
2. Frontend automatically calls `/api/v1/auth/login-anonymous`
3. Backend generates JWT token for anonymous user
4. Token stored in localStorage and used for all API calls
5. Token automatically refreshed when expired

#### JWT Token Structure
```json
{
  "sub": "1",
  "username": "anonymous", 
  "email": "anonymous@archaeologist.local",
  "is_admin": false,
  "exp": 1738339200,
  "iat": 1735747200
}
```

## Files Created/Modified

### Backend Files
- `api/app/auth_service.py` - JWT token management service
- `api/app/routes/auth.py` - Authentication endpoints
- `api/app/routes/projects.py` - Project management endpoints
- `api/dependencies/auth.py` - Authentication dependencies
- `api/models/database.py` - Added Project, ProjectUser, ProjectRole models
- `api/db/base.py` - Added project management abstract methods
- `api/db/sqlite.py` - Added project and user table schemas
- `api/app/config.py` - Added JWT configuration
- `api/app/main.py` - Integrated authentication routes and dependencies
- `.env.dev` / `.env.prod` - Added JWT secret key configuration

### Frontend Files
- `ui/src/contexts/AuthContext.tsx` - Authentication state management (in-memory)
- `ui/src/utils/apiClient.ts` - API client with Vite proxying
- `ui/src/App.tsx` - Updated with login screen handling
- `ui/src/components/LoginPage.tsx` - Login page component
- `ui/src/components/LoginPage.css` - Login page styling
- `ui/src/App.css` - Updated with loading/login screen styles

### Test Files
- `test_auth.py` - Authentication system validation script (removed)

## Security Features

### JWT Implementation
- **HS256 Algorithm**: Secure JWT signing with configurable secret keys
- **Token Expiration**: 30-day tokens for prototype (configurable)
- **Automatic Refresh**: Seamless token refresh on expiration
- **Stateless Authentication**: No server-side session storage required

### Access Control
- **Role-Based Permissions**: Hierarchical access control by project role
- **Project Isolation**: Users can only access projects they're members of
- **Endpoint Protection**: All protected endpoints require valid JWT tokens
- **Optional Authentication**: Some endpoints support optional anonymous access

## Environment Configuration

### Development (.env.dev)
```
JWT_SECRET_KEY=development-secret-key-change-in-production-this-is-not-secure
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days
```

### Production (.env.prod)
```
JWT_SECRET_KEY=change-this-secret-key-in-production-its-not-secure
JWT_ALGORITHM=HS256  
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days
```

## Usage Examples

### API Usage
```bash
# Get anonymous token
curl -X POST http://localhost:8000/api/v1/auth/login-anonymous \
  -H "Content-Type: application/json" \
  -d '{"username": "anonymous", "password": "anonymous"}'

# Use token for API calls
curl -X GET http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Frontend Usage
```typescript
// Authentication context automatically handles everything
import { useAuth } from './contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, logout } = useAuth();
  
  // Component automatically handles authentication state
}
```

## Next Steps

1. **Run the Application**: `./deploy.sh dev`
2. **Test Authentication**: Visit http://localhost:8000
3. **Explore Projects**: Use the UI or API to manage projects
4. **Extend Roles**: Add custom roles for specific use cases
5. **Enhance Security**: Add rate limiting, CSRF protection for production
6. **User Registration**: Implement full user registration flow
7. **Multi-tenant UI**: Add project selection UI components

## Notes

- **Prototype Design**: Current implementation focuses on anonymous access for testing
- **Production Ready**: Foundation is in place for full user authentication
- **Database Independent**: Uses abstract base class for easy database switching
- **React Compatible**: Uses modern React patterns with TypeScript
- **API First**: Complete REST API for all operations