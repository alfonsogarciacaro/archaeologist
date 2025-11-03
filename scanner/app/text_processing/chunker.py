"""
Text Chunker

This module provides intelligent text chunking with overlap and code-aware splitting,
optimized for embedding models in RAG systems.
"""

import re
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logging.warning("tiktoken not available, using character-based chunking")

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    text: str
    chunk_id: str
    start_index: int
    end_index: int
    token_count: int
    metadata: Dict[str, Any]


class TextChunker:
    """
    Intelligent text chunker with overlap and code-aware splitting.
    
    This chunker is optimized for embedding models and provides:
    - Token-based chunking using tiktoken
    - Configurable overlap between chunks
    - Code-aware splitting at logical boundaries
    - Metadata preservation for each chunk
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
        encoding_name: str = "cl100k_base",  # GPT-4 tokenizer, works well for code
        code_aware: bool = True
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            min_chunk_size: Minimum chunk size in tokens
            encoding_name: Name of the tiktoken encoding to use
            code_aware: Whether to use code-aware splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.encoding_name = encoding_name
        self.code_aware = code_aware
        
        # Initialize tokenizer
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.get_encoding(encoding_name)
                logger.info(f"Using tiktoken encoding: {encoding_name}")
            except Exception as e:
                logger.error(f"Failed to load tiktoken encoding {encoding_name}: {e}")
                self.tokenizer = None
        else:
            self.tokenizer = None
        
        # Code splitting patterns
        self.code_patterns = {
            'python': [
                r'\ndef\s+\w+\s*\([^)]*\)\s*:',  # Function definitions
                r'\nclass\s+\w+\s*\([^)]*\)\s*:',  # Class definitions
                r'\n\s*def\s+\w+\s*\([^)]*\)\s*:',  # Indented functions
                r'\n\s*class\s+\w+\s*\([^)]*\)\s*:',  # Indented classes
                r'\nif\s+__name__\s*==\s*["\']__main__["\']\s*:',  # Main block
            ],
            'javascript': [
                r'\nfunction\s+\w+\s*\([^)]*\)\s*{',  # Function definitions
                r'\nconst\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{',  # Arrow functions
                r'\nclass\s+\w+\s*{',  # Class definitions
                r'\n\s*function\s+\w+\s*\([^)]*\)\s*{',  # Indented functions
            ],
            'sql': [
                r'\n(CREATE|ALTER|DROP)\s+(TABLE|INDEX|VIEW|PROCEDURE|FUNCTION)\s+\w+',  # DDL
                r'\n(INSERT|UPDATE|DELETE|SELECT)\s+',  # DML
                r'\n--.*$',  # SQL comments
            ],
            'general': [
                r'\n#{1,6}\s+',  # Markdown headers
                r'\n\n',  # Paragraph breaks
                r'\n\s*[-*+]\s+',  # List items
                r'\n\s*\d+\.\s+',  # Numbered lists
            ]
        }
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the configured tokenizer.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def split_text_aware(self, text: str, file_type: str = 'general') -> List[str]:
        """
        Split text at code-aware boundaries.
        
        Args:
            text: Text to split
            file_type: Type of file ('python', 'javascript', 'sql', 'general')
            
        Returns:
            List of text segments
        """
        if not self.code_aware:
            return [text]
        
        # Get relevant patterns for file type
        patterns = []
        if file_type in self.code_patterns:
            patterns.extend(self.code_patterns[file_type])
        patterns.extend(self.code_patterns['general'])
        
        # Try each pattern to find good split points
        split_points = [0]  # Always include start
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                split_points.append(match.start())
        
        # Sort and deduplicate split points
        split_points = sorted(list(set(split_points)))
        
        # Create segments
        segments = []
        for i in range(len(split_points)):
            start = split_points[i]
            end = split_points[i + 1] if i + 1 < len(split_points) else len(text)
            
            if end > start:
                segment = text[start:end].strip()
                if segment:
                    segments.append(segment)
        
        return segments
    
    def create_chunks_with_overlap(self, text: str, file_type: str = 'general') -> List[TextChunk]:
        """
        Create chunks with overlap from text.
        
        Args:
            text: Text to chunk
            file_type: Type of file for code-aware splitting
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
        
        start_time = time.time()
        
        # First, split text at logical boundaries
        segments = self.split_text_aware(text, file_type)
        logger.debug(f"Split text into {len(segments)} segments")
        
        # Create chunks from segments
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for segment in segments:
            # Check if adding this segment would exceed chunk size
            test_chunk = current_chunk + ("\n\n" if current_chunk else "") + segment
            test_tokens = self.count_tokens(test_chunk)
            
            if test_tokens <= self.chunk_size and current_chunk:
                # Add to current chunk
                current_chunk = test_chunk
            else:
                # Save current chunk if it's large enough
                if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
                    chunk = TextChunk(
                        text=current_chunk.strip(),
                        chunk_id=f"chunk_{chunk_id}",
                        start_index=current_start,
                        end_index=current_start + len(current_chunk),
                        token_count=self.count_tokens(current_chunk),
                        metadata={
                            "file_type": file_type,
                            "creation_method": "overlap_chunking"
                        }
                    )
                    chunks.append(chunk)
                    chunk_id += 1
                
                # Start new chunk with overlap
                if current_chunk:
                    # Calculate overlap
                    overlap_tokens = self.chunk_overlap
                    if self.tokenizer:
                        # Get overlap text by tokens
                        current_tokens = self.tokenizer.encode(current_chunk)
                        overlap_tokens_list = current_tokens[-overlap_tokens:] if len(current_tokens) > overlap_tokens else current_tokens
                        overlap_text = self.tokenizer.decode(overlap_tokens_list)
                        current_chunk = overlap_text + "\n\n" + segment
                    else:
                        # Fallback: character-based overlap
                        overlap_chars = overlap_tokens * 4
                        overlap_text = current_chunk[-overlap_chars:] if len(current_chunk) > overlap_chars else current_chunk
                        current_chunk = overlap_text + "\n\n" + segment
                else:
                    current_chunk = segment
                
                current_start = len(text) - len(current_chunk)
        
        # Don't forget the last chunk
        if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
            chunk = TextChunk(
                text=current_chunk.strip(),
                chunk_id=f"chunk_{chunk_id}",
                start_index=current_start,
                end_index=len(text),
                token_count=self.count_tokens(current_chunk),
                metadata={
                    "file_type": file_type,
                    "creation_method": "overlap_chunking"
                }
            )
            chunks.append(chunk)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Created {len(chunks)} chunks in {elapsed_time:.3f}s")
        
        return chunks
    
    def chunk_document(
        self,
        content: str,
        file_name: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        Chunk a complete document.
        
        Args:
            content: Document content
            file_name: Name of the file
            file_type: Type of file (inferred from extension if not provided)
            metadata: Additional metadata to include in chunks
            
        Returns:
            List of TextChunk objects
        """
        start_time = time.time()
        
        # Infer file type from extension if not provided
        if file_type is None:
            ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            file_type_map = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'javascript',
                'sql': 'sql',
                'jsx': 'javascript',
                'tsx': 'javascript',
            }
            file_type = file_type_map.get(ext, 'general')
        
        # Create chunks
        chunks = self.create_chunks_with_overlap(content, file_type)
        
        # Add file metadata to each chunk
        file_metadata = {
            "file_name": file_name,
            "file_type": file_type,
            "total_chunks": len(chunks),
            "chunking_strategy": "overlap_aware"
        }
        
        if metadata:
            file_metadata.update(metadata)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata.update(file_metadata)
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Chunked document '{file_name}' into {len(chunks)} chunks in {elapsed_time:.3f}s")
        
        return chunks
    
    def get_chunking_stats(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Get statistics about the chunks.
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            Dictionary with chunking statistics
        """
        if not chunks:
            return {"total_chunks": 0}
        
        token_counts = [chunk.token_count for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) / len(token_counts),
            "min_tokens_per_chunk": min(token_counts),
            "max_tokens_per_chunk": max(token_counts),
            "chunk_size_target": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_size": self.min_chunk_size
        }