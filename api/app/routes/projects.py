"""
Project management routes.

This module provides endpoints for creating, managing, and accessing projects
and their user permissions.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from dependencies.auth import get_current_user_id
from dependencies.database import get_database
from db import DatabaseAbc
from models.database import ProjectRole

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Project creation request model."""
    name: str
    description: Optional[str] = None
    repository_paths: Optional[List[str]] = None


class ProjectUpdate(BaseModel):
    """Project update request model."""
    name: Optional[str] = None
    description: Optional[str] = None
    repository_paths: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    """Project response model with additional metadata."""
    id: int
    name: str
    description: Optional[str] = None
    repository_paths: Optional[List[str]] = None
    is_active: bool
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_role: Optional[str] = None  # Current user's role in this project


class ProjectUserAdd(BaseModel):
    """Add user to project request model."""
    user_id: int
    role: str


class ProjectUserUpdate(BaseModel):
    """Update user role in project request model."""
    role: str


class UserWithRole(BaseModel):
    """User information with project role."""
    id: int
    username: str
    email: str
    is_active: bool
    role: str
    created_at: Optional[datetime] = None


async def check_project_access(
    project_id: int,
    user_id: int,
    db: DatabaseAbc,
    required_roles: List[str] | None = None
) -> str:
    """
    Check if user has access to the project and return their role.
    
    Args:
        project_id: ID of the project
        user_id: Current user ID
        db: Database instance
        required_roles: List of roles that can access (None for any role)
    
    Returns:
        User's role in the project
    
    Raises:
        HTTPException: If user doesn't have access
    """


    user_role = await db.get_user_project_role(project_id, user_id)
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    if required_roles and user_role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Requires one of: {', '.join(required_roles)}"
        )
    
    return user_role


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Create a new project."""
    project = await db.create_project(
        name=project_data.name,
        description=project_data.description,
        repository_paths=project_data.repository_paths,
        created_by=current_user_id
    )
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        repository_paths=project.repository_paths,
        is_active=project.is_active,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        user_role="owner"  # Creator is always owner
    )


@router.get("", response_model=List[ProjectResponse])
async def get_user_projects(
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get all projects accessible to the current user."""
    projects = await db.get_user_projects(current_user_id)
    
    project_responses = []
    for project in projects:
        user_role = await db.get_user_project_role(project.id, current_user_id)
        
        project_responses.append(ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            repository_paths=project.repository_paths,
            is_active=project.is_active,
            created_by=project.created_by,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_role=user_role
        ))
    
    return project_responses


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get a specific project by ID."""
    # Check user access
    user_role = await check_project_access(project_id, current_user_id, db)
    
    project = await db.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        repository_paths=project.repository_paths,
        is_active=project.is_active,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        user_role=user_role
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Update a project."""
    # Check user has admin or owner role
    user_role = await check_project_access(
        project_id, current_user_id, db, 
        [ProjectRole.OWNER, ProjectRole.ADMIN]
    )
    
    # Build update data
    update_data = {}
    if project_data.name is not None:
        update_data['name'] = project_data.name
    if project_data.description is not None:
        update_data['description'] = project_data.description
    if project_data.repository_paths is not None:
        update_data['repository_paths'] = project_data.repository_paths
    if project_data.is_active is not None:
        update_data['is_active'] = project_data.is_active
    
    if update_data:
        await db.update_project(project_id, **update_data)
    
    # Get updated project
    project = await db.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        repository_paths=project.repository_paths,
        is_active=project.is_active,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        user_role=user_role
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Delete (deactivate) a project."""
    # Only owners can delete projects
    await check_project_access(
        project_id, current_user_id, db, 
        [ProjectRole.OWNER]
    )
    
    await db.delete_project(project_id)
    
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/users", response_model=List[UserWithRole])
async def get_project_users(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get all users in a project."""
    # Check user access
    user_role = await check_project_access(project_id, current_user_id, db)
    
    project_users = await db.get_project_users(project_id)
    
    users_with_roles = []
    for project_user in project_users:
        user = await db.get_user_by_id(project_user.user_id)
        if user:
            users_with_roles.append(UserWithRole(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                role=project_user.role,
                created_at=project_user.created_at
            ))
    
    return users_with_roles


@router.post("/{project_id}/users", response_model=UserWithRole)
async def add_user_to_project(
    project_id: int,
    add_data: ProjectUserAdd,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Add a user to a project."""
    # Check user has admin or owner role
    await check_project_access(
        project_id, current_user_id, db, 
        [ProjectRole.OWNER, ProjectRole.ADMIN]
    )
    
    # Validate role
    if add_data.role not in [r.value for r in ProjectRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in ProjectRole]}"
        )
    
    # Check if user exists
    target_user = await db.get_user_by_id(add_data.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Add user to project
    project_user = await db.add_user_to_project(
        project_id, add_data.user_id, add_data.role
    )
    
    return UserWithRole(
        id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        is_active=target_user.is_active,
        role=project_user.role,
        created_at=project_user.created_at
    )


@router.put("/{project_id}/users/{user_id}")
async def update_user_project_role(
    project_id: int,
    user_id: int,
    update_data: ProjectUserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Update a user's role in a project."""
    # Only owners can change roles
    await check_project_access(
        project_id, current_user_id, db, 
        [ProjectRole.OWNER]
    )
    
    # Validate role
    if update_data.role not in [r.value for r in ProjectRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in ProjectRole]}"
        )
    
    # Cannot change own role
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Update user role
    success = await db.update_user_project_role(
        project_id, user_id, update_data.role
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in project"
        )
    
    return {"message": "User role updated successfully"}


@router.delete("/{project_id}/users/{user_id}")
async def remove_user_from_project(
    project_id: int,
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Remove a user from a project."""
    # Check user has admin or owner role (or is removing self)
    user_role = await check_project_access(project_id, current_user_id, db)
    
    if user_id != current_user_id and user_role not in [ProjectRole.OWNER, ProjectRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or owners can remove other users"
        )
    
    # Cannot remove the last owner
    if user_role == ProjectRole.OWNER:
        project_users = await db.get_project_users(project_id)
        owners = [pu for pu in project_users if pu.role == ProjectRole.OWNER]
        if len(owners) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner from the project"
            )
    
    await db.remove_user_from_project(project_id, user_id)
    
    return {"message": "User removed from project successfully"}