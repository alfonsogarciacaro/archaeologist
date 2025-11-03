"""
Project management routes.

This module provides endpoints for creating, managing, and accessing projects
and their user permissions.
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import zipfile
import io
import json
from pathlib import Path

from dependencies.auth import get_current_user_id
from dependencies.database import get_database
from db import DatabaseAbc
from models.database import ProjectRole, Source
from app.data_lake_interface import DataType
from app.disk_data_lake import DiskDataLake

router = APIRouter(prefix="/projects", tags=["projects"])

# Initialize data lake
data_lake = DiskDataLake(base_path="data_lake")


def is_text_file(filename: str, content: bytes) -> bool:
    """Check if a file is a text file based on extension and content."""
    text_extensions = {
        '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json',
        '.xml', '.yaml', '.yml', '.md', '.sql', '.sh', '.bash', '.zsh',
        '.cfg', '.conf', '.ini', '.toml', '.env', '.log', '.csv', '.tsv'
    }

    # Check extension
    ext = Path(filename).suffix.lower()
    if ext in text_extensions:
        return True

    # Check content for common text patterns (limited check for safety)
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


async def process_file_content(
    file: UploadFile,
    project_id: int,
    current_user_id: int,
    db: DatabaseAbc,
    user_metadata: Optional[Dict[str, Any]] = None
) -> Optional[Source]:
    """Process a single uploaded file and store it in the data lake."""
    try:
        # Read file content
        content_bytes = await file.read()
        file_size = len(content_bytes)

        # Reset file position for potential re-reading
        await file.seek(0)

        # Determine content type
        filename = file.filename or "unknown"
        if filename.lower().endswith('.zip'):
            content_type = "zip"
        elif is_text_file(filename, content_bytes):
            content_type = "text"
        else:
            return None  # Skip unsupported file types

        # Generate unique filename
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        # Store in data lake
        project_subpath = f"projects/{project_id}"

        if content_type == "zip":
            # Handle zip file extraction
            content_str = ""
            extracted_files = []

            try:
                zip_content = await file.read()
                await file.seek(0)

                with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        if not file_info.is_dir():
                            try:
                                extracted_content = zip_ref.read(file_info.filename)

                                if is_text_file(file_info.filename, extracted_content):
                                    extracted_text = extracted_content.decode('utf-8', errors='ignore')

                                    # Store each extracted file in data lake
                                    extracted_filename = f"{uuid.uuid4()}_{Path(file_info.filename).name}"
                                    await data_lake.store(
                                        name=extracted_filename,
                                        content=extracted_text,
                                        data_type=DataType.OTHER,
                                        metadata={
                                            "original_filename": file_info.filename,
                                            "project_id": str(project_id),
                                            "extracted_from_zip": filename,
                                            "file_size": len(extracted_content)
                                        },
                                        subpath=project_subpath
                                    )

                                    extracted_files.append({
                                        "filename": file_info.filename,
                                        "size": len(extracted_content)
                                    })

                                    content_str += f"\n\n--- File: {file_info.filename} ---\n{extracted_text}"
                            except Exception as e:
                                print(f"Error extracting file {file_info.filename}: {e}")
                                continue

                if not extracted_files:
                    return None  # No text files found in zip

                # Store the zip manifest
                manifest_content = f"Zip file: {filename}\nExtracted files:\n"
                for extracted in extracted_files:
                    manifest_content += f"- {extracted['filename']} ({extracted['size']} bytes)\n"

                data_lake_entry = await data_lake.store(
                    name=unique_filename,
                    content=manifest_content,
                    data_type=DataType.OTHER,
                    metadata={
                        "original_filename": filename,
                        "project_id": str(project_id),
                        "file_type": "zip",
                        "file_size": file_size,
                        "extracted_files_count": len(extracted_files),
                        "extracted_files": extracted_files
                    },
                    subpath=project_subpath
                )

            except zipfile.BadZipFile:
                return None  # Invalid zip file

        else:
            # Handle text file
            content_str = content_bytes.decode('utf-8', errors='ignore')

            data_lake_entry = await data_lake.store(
                name=unique_filename,
                content=content_str,
                data_type=DataType.OTHER,
                metadata={
                    "original_filename": filename,
                    "project_id": str(project_id),
                    "file_type": "text",
                    "file_size": file_size
                },
                subpath=project_subpath
            )

        # Create source record in database
        source = await db.create_source(
            project_id=project_id,
            filename=unique_filename,
            original_filename=filename,
            file_size=file_size,
            file_type=file.content_type or "application/octet-stream",
            content_type=content_type,
            data_lake_entry_id=data_lake_entry.id,
            uploaded_by=current_user_id,
            metadata=user_metadata  # Only store user-provided metadata in DB
        )

        return source

    except Exception as e:
        print(f"Error processing file {file.filename}: {e}")
        return None


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


class SourceResponse(BaseModel):
    """Source response model."""
    id: int
    project_id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    content_type: str
    uploaded_by: int
    created_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class FileUploadResponse(BaseModel):
    """File upload response model."""
    success: bool
    message: str
    sources: List[SourceResponse]
    total_files: int
    processed_files: int
    skipped_files: int


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


@router.post("", response_model=ProjectResponse)
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


@router.post("/{project_id}/upload", response_model=FileUploadResponse)
async def upload_project_sources(
    project_id: int,
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None),
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Upload source files to a project."""
    # Check user access
    await check_project_access(project_id, current_user_id, db)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    processed_sources = []
    total_files = len(files)
    skipped_files = 0
    
    # Parse metadata if provided
    parsed_metadata = None
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            # If metadata is not valid JSON, treat as a simple comment
            parsed_metadata = {"comment": metadata}

    for file in files:
        if not file.filename:
            skipped_files += 1
            continue

        try:
            source = await process_file_content(
                file, project_id, current_user_id, db, parsed_metadata
            )

            if source:
                processed_sources.append(SourceResponse(
                    id=source.id,
                    project_id=source.project_id,
                    filename=source.filename,
                    original_filename=source.original_filename,
                    file_size=source.file_size,
                    file_type=source.file_type,
                    content_type=source.content_type,
                    uploaded_by=source.uploaded_by,
                    created_at=source.created_at,
                    metadata=source.metadata
                ))
            else:
                skipped_files += 1

        except Exception as e:
            print(f"Error processing file {file.filename}: {e}")
            skipped_files += 1
            continue

    processed_files = len(processed_sources)

    if processed_files == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No supported files were processed. Please upload text files (.txt, .py, .js, etc.) or zip files containing text files."
        )

    return FileUploadResponse(
        success=True,
        message=f"Successfully processed {processed_files} out of {total_files} files. {skipped_files} files were skipped.",
        sources=processed_sources,
        total_files=total_files,
        processed_files=processed_files,
        skipped_files=skipped_files
    )


@router.get("/{project_id}/sources", response_model=List[SourceResponse])
async def get_project_sources(
    project_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Get all sources for a project."""
    # Check user access
    await check_project_access(project_id, current_user_id, db)

    sources = await db.get_project_sources(project_id)

    return [
        SourceResponse(
            id=source.id,
            project_id=source.project_id,
            filename=source.filename,
            original_filename=source.original_filename,
            file_size=source.file_size,
            file_type=source.file_type,
            content_type=source.content_type,
            uploaded_by=source.uploaded_by,
            created_at=source.created_at,
            metadata=source.metadata
        )
        for source in sources
    ]


@router.delete("/{project_id}/sources/{source_id}")
async def delete_project_source(
    project_id: int,
    source_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Delete a source from a project."""
    # Check user has admin or owner role
    await check_project_access(
        project_id, current_user_id, db,
        [ProjectRole.OWNER, ProjectRole.ADMIN]
    )

    # Get source to verify it belongs to the project
    source = await db.get_source_by_id(source_id)
    if not source or source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found in this project"
        )

    # Delete from database (data lake cleanup could be added here)
    success = await db.delete_source(source_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete source"
        )

    return {"message": "Source deleted successfully"}


@router.put("/{project_id}/sources/{source_id}/metadata")
async def update_source_metadata(
    project_id: int,
    source_id: int,
    metadata: Dict[str, Any],
    current_user_id: int = Depends(get_current_user_id),
    db: DatabaseAbc = Depends(get_database)
):
    """Update metadata for a source."""
    # Check user has admin or owner role
    await check_project_access(
        project_id, current_user_id, db,
        [ProjectRole.OWNER, ProjectRole.ADMIN]
    )

    # Get source to verify it belongs to the project
    source = await db.get_source_by_id(source_id)
    if not source or source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found in this project"
        )

    # Update source metadata
    success = await db.update_source_metadata(source_id, metadata)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update source metadata"
        )

    return {"message": "Source metadata updated successfully", "metadata": metadata}