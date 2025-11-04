"""
Job manager for handling different types of processing jobs.

This module provides the main job processing logic that handles
file processing, batch processing, and investigation jobs.
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from .scanner.rag.rag_service import get_rag_service
from .scanner.rag.models import IngestRequest
from .config import get_settings

logger = logging.getLogger(__name__)


class JobManager:
    """Manages job processing for different job types."""

    def __init__(self):
        self.settings = get_settings()
        self.data_lake_base_path = "data_lake"

    async def process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a job based on its type.

        Args:
            job: Job data dictionary

        Returns:
            Job result data
        """
        job_type = job.get("job_type", "unknown")
        job_id = job.get("id", "unknown")

        logger.info(f"Processing job {job_id} of type {job_type}")

        try:
            if job_type == "file_processing":
                return await self._process_file_job(job)
            elif job_type == "batch_processing":
                return await self._process_batch_job(job)
            elif job_type == "investigation":
                return await self._process_investigation_job(job)
            else:
                raise ValueError(f"Unknown job type: {job_type}")

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            raise

    async def _process_file_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a file processing job.

        This job type handles:
        - Retrieving file content from data lake
        - Chunking and creating embeddings
        - Storing in vector database
        """
        job_id = job.get("id")
        job_data = job.get("job_data", {})
        project_id = job_data.get("project_id")
        source_id = job_data.get("source_id")
        filename = job_data.get("filename")
        original_filename = job_data.get("original_filename")
        data_lake_entry_id = job_data.get("data_lake_entry_id")

        logger.info(f"Processing file job {job_id}: {original_filename}")

        # Update progress
        from .job_client import job_client
        await job_client.update_job_progress(job_id, 1, 5, "Retrieving file from data lake...")

        try:
            # Retrieve file content from data lake
            content = await self._get_file_content(data_lake_entry_id, project_id)
            if not content:
                raise ValueError(f"File content not found for entry: {data_lake_entry_id}")

            await job_client.update_job_progress(job_id, 2, 5, "Preparing document for ingestion...")

            # Prepare ingestion request
            file_type = self._determine_file_type(original_filename, content)
            collection_name = f"project_{project_id}_source_{source_id}"

            ingest_request = IngestRequest(
                file_name=original_filename,
                project=f"project_{project_id}",
                content=content,
                file_type=file_type,
                timestamp=job.get("created_at"),
                metadata={
                    "source_id": source_id,
                    "project_id": project_id,
                    "original_filename": original_filename,
                    "job_id": job_id,
                    **job_data.get("user_metadata", {})
                }
            )

            await job_client.update_job_progress(job_id, 3, 5, "Generating embeddings and storing chunks...")

            # Ingest into RAG system
            rag_service = await get_rag_service()
            result = await rag_service.ingest_document(ingest_request)

            await job_client.update_job_progress(job_id, 5, 5, "File processing completed")

            # Return result
            return {
                "success": True,
                "chunks_created": result.chunks_created,
                "collection_name": result.collection_name,
                "file_type": file_type,
                "source_id": source_id,
                "project_id": project_id,
                "processing_time_ms": result.processing_time_ms
            }

        except Exception as e:
            logger.error(f"Error processing file job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "source_id": source_id,
                "project_id": project_id
            }

    async def _process_batch_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a batch processing job.

        This job type handles processing multiple files or large datasets.
        """
        job_id = job.get("id")
        job_data = job.get("job_data", {})

        logger.info(f"Processing batch job {job_id}")

        # TODO: Implement batch processing logic
        # This could handle multiple files, large datasets, etc.

        return {
            "success": True,
            "message": "Batch processing completed",
            "files_processed": 0
        }

    async def _process_investigation_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an investigation job.

        This job type handles LLM-powered code investigation and analysis.
        """
        job_id = job.get("id")
        job_data = job.get("job_data", {})

        logger.info(f"Processing investigation job {job_id}")

        # TODO: Implement investigation processing logic
        # This could run comprehensive code analysis using LLM

        return {
            "success": True,
            "message": "Investigation completed",
            "nodes_found": 0,
            "relationships_found": 0
        }

    async def _get_file_content(self, data_lake_entry_id: str, project_id: int) -> Optional[str]:
        """
        Retrieve file content from the data lake.

        Args:
            data_lake_entry_id: ID of the data lake entry
            project_id: Project ID for path construction

        Returns:
            File content as string, or None if not found
        """
        try:
            # Construct file path in data lake
            # Data lake structure: data_lake/projects/{project_id}/{filename}
            data_lake_path = Path(self.data_lake_base_path)
            project_path = data_lake_path / "projects" / str(project_id)

            # Try to find the file by entry_id (filename)
            for file_path in project_path.glob("*"):
                if file_path.name == data_lake_entry_id or file_path.stem == data_lake_entry_id:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    return content

            # If not found by exact match, try to read the file directly
            direct_path = project_path / data_lake_entry_id
            if direct_path.exists():
                content = direct_path.read_text(encoding='utf-8', errors='ignore')
                return content

            logger.warning(f"File not found in data lake: {data_lake_entry_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving file content from data lake: {e}")
            return None

    def _determine_file_type(self, filename: str, content: str) -> str:
        """
        Determine file type based on filename and content.

        Args:
            filename: Original filename
            content: File content

        Returns:
            File type string
        """
        # Get file extension
        ext = Path(filename).suffix.lower()

        # Map extensions to file types
        type_mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.md': 'markdown',
            '.txt': 'text',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch',
        }

        file_type = type_mapping.get(ext, 'text')

        # Additional content-based detection
        if file_type == 'text':
            # Check for common patterns in content
            content_lower = content.lower()

            if 'def ' in content and 'import ' in content:
                file_type = 'python'
            elif 'function ' in content and 'const ' in content:
                file_type = 'javascript'
            elif 'class ' in content and 'public ' in content:
                file_type = 'java'
            elif 'create table' in content or 'select ' in content:
                file_type = 'sql'

        return file_type


# Global job manager instance
job_manager = JobManager()