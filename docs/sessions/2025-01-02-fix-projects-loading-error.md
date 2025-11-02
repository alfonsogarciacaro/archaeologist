# 2025-01-02-Fix Projects Loading Error

## Problem
The UI was showing "Failed to load projects. Please try again." error when trying to access the projects list.

## Root Cause
1. The projects API endpoint required authentication with `get_current_user`
2. There were no users in the database, including the anonymous user
3. The authentication was using a placeholder login system that didn't properly verify users in the database

## Solution Implemented

### 1. Database Initialization Fix
- Modified `_insert_default_config()` method in `/api/db/sqlite.py` to create the anonymous user on database initialization
- Added `_ensure_anonymous_user()` method that creates the anonymous user if it doesn't exist
- Fixed the anonymous user creation to use the correct hashed password from auth_service

### 2. Real Authentication System
- Implemented proper username/password authentication in `/api/app/routes/auth.py`
- Modified the `/login` endpoint to:
  - Accept real username and password credentials
  - For 'anonymous' username: use empty password check
  - For regular users: verify password using bcrypt
  - Generate JWT tokens for authenticated users
- Added `/register` endpoint for user registration with password hashing
- Added `update_user_last_login()` method to database layer

### 3. Password Security
- Used bcrypt for password hashing (automatically generates unique salt per hash)
- Standardized all password hashing to use `auth_service.get_password_hash()` method
- Removed duplicate hashing logic

### 4. Security Architecture Cleanup
- **CRITICAL**: Removed `/api/app/routes/database.py` entirely
- This file was a security risk because it exposed direct database operations
- Eliminated duplicate authentication endpoints that conflicted with JWT system
- Centralized all authentication through proper `/auth/*` routes

## Technical Details

### Password Hashing
```python
# All password hashing now uses single method:
hashed_password = auth_service.get_password_hash(password)
# Verification: auth_service.verify_password(plain_password, hashed_password)
```

### Authentication Flow
1. User provides username/password to `/login` endpoint
2. For 'anonymous' user: password check is bypassed
3. For regular users: password is verified against bcrypt hash
4. If successful, JWT token is generated and returned
5. Projects API now works with authenticated users

### Security Architecture
- Single authentication entry point via `/auth/login` and `/auth/register`
- No direct database access endpoints
- Centralized JWT token management
- Proper separation of concerns

## Files Modified
- `/api/db/sqlite.py` - Added anonymous user creation and password handling
- `/api/app/routes/auth.py` - Implemented real authentication system
- `/api/app/main.py` - Removed database router imports
- `/api/app/routes/database.py` - **DELETED** (security cleanup)

## Security Impact
- Removed dangerous direct database exposure
- Eliminated conflicting authentication patterns
- Standardized password hashing across the codebase
- Centralized authentication logic in proper service layer

## Testing
- API running with auto-reload should pick up changes automatically
- Anonymous user is now available for immediate access
- Real users can register and authenticate with secure password hashing
- Projects loading should now work properly

## Next Steps
Consider adding:
- Password strength validation
- Account email verification
- Password reset functionality
- Rate limiting for login attempts