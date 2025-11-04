"""
Text Preprocessor

This module provides text preprocessing functionality for the RAG system,
including code normalization, comment handling, and content filtering.
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """
    Text preprocessor for code and documentation.
    
    This preprocessor handles:
    - Code normalization and formatting
    - Comment and documentation extraction
    - Noise reduction and filtering
    - Language-specific preprocessing
    """
    
    def __init__(
        self,
        remove_comments: bool = False,
        normalize_whitespace: bool = True,
        min_line_length: int = 1,
        max_line_length: int = 10000,
        preserve_structure: bool = True
    ):
        """
        Initialize text preprocessor.
        
        Args:
            remove_comments: Whether to remove code comments
            normalize_whitespace: Whether to normalize whitespace
            min_line_length: Minimum line length to keep
            max_line_length: Maximum line length before truncation
            preserve_structure: Whether to preserve code structure
        """
        self.remove_comments = remove_comments
        self.normalize_whitespace = normalize_whitespace
        self.min_line_length = min_line_length
        self.max_line_length = max_line_length
        self.preserve_structure = preserve_structure
        
        # Language-specific comment patterns
        self.comment_patterns = {
            'python': [
                (r'#.*$', None),  # Single line comments
                (r'""".*?"""', None),  # Multi-line docstrings
                (r"'''.*?'''", None),  # Multi-line docstrings
            ],
            'javascript': [
                (r'//.*$', None),  # Single line comments
                (r'/\*.*?\*/', None),  # Multi-line comments
            ],
            'sql': [
                (r'--.*$', None),  # Single line comments
                (r'/\*.*?\*/', None),  # Multi-line comments
            ],
            'general': [
                (r'<!--.*?-->', None),  # HTML/XML comments
            ]
        }
        
        # Language-specific string patterns to preserve
        self.string_patterns = {
            'python': [
                (r'""".*?"""', 'STRING'),
                (r"'''.*?'''", 'STRING'),
                (r'"[^"]*"', 'STRING'),
                (r"'[^']*'", 'STRING'),
            ],
            'javascript': [
                (r'`[^`]*`', 'STRING'),  # Template literals
                (r'"[^"]*"', 'STRING'),
                (r"'[^']*'", 'STRING'),
            ],
            'sql': [
                (r"'[^']*'", 'STRING'),
                (r'"[^"]*"', 'STRING'),
            ]
        }
    
    def detect_language(self, content: str, file_name: str) -> str:
        """
        Detect the programming language of the content.
        
        Args:
            content: Text content to analyze
            file_name: Name of the file
            
        Returns:
            Detected language ('python', 'javascript', 'sql', 'general')
        """
        # Check file extension first
        ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
        ext_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'javascript',
            'jsx': 'javascript',
            'tsx': 'javascript',
            'sql': 'sql',
            'vue': 'javascript',
            'html': 'general',
            'css': 'general',
            'md': 'general',
            'txt': 'general',
        }
        
        if ext in ext_map:
            return ext_map[ext]
        
        # Analyze content patterns
        content_lower = content.lower()
        
        # Python indicators
        if any(pattern in content_lower for pattern in ['def ', 'import ', 'from import', 'class ', 'if __name__']):
            return 'python'
        
        # JavaScript indicators
        if any(pattern in content_lower for pattern in ['function ', 'const ', 'let ', 'var ', '=>', 'require(', 'import ']):
            return 'javascript'
        
        # SQL indicators
        if any(pattern in content_lower for pattern in ['select ', 'from ', 'where ', 'insert into', 'create table', 'update ']):
            return 'sql'
        
        return 'general'
    
    def preserve_strings(self, content: str, language: str) -> tuple[str, List[str]]:
        """
        Replace strings with placeholders to avoid processing them.
        
        Args:
            content: Text content
            language: Programming language
            
        Returns:
            Tuple of (content_with_placeholders, list_of_strings)
        """
        if language not in self.string_patterns:
            return content, []
        
        strings = []
        modified_content = content
        
        for pattern, _ in self.string_patterns[language]:
            def replace_string(match):
                strings.append(match.group(0))
                return f"__STRING_{len(strings)-1}__"
            
            modified_content = re.sub(pattern, replace_string, modified_content, flags=re.DOTALL)
        
        return modified_content, strings
    
    def restore_strings(self, content: str, strings: List[str]) -> str:
        """
        Restore strings from placeholders.
        
        Args:
            content: Content with placeholders
            strings: List of original strings
            
        Returns:
            Content with restored strings
        """
        for i, string in enumerate(strings):
            content = content.replace(f"__STRING_{i}__", string)
        return content
    
    def remove_comments_from_content(self, content: str, language: str) -> str:
        """
        Remove comments from content based on language.
        
        Args:
            content: Text content
            language: Programming language
            
        Returns:
            Content with comments removed
        """
        if language not in self.comment_patterns:
            return content
        
        # Preserve strings first
        content_with_placeholders, strings = self.preserve_strings(content, language)
        
        # Remove comments
        modified_content = content_with_placeholders
        
        for pattern, _ in self.comment_patterns[language]:
            modified_content = re.sub(pattern, '', modified_content, flags=re.MULTILINE | re.DOTALL)
        
        # Restore strings
        return self.restore_strings(modified_content, strings)
    
    def normalize_whitespace_content(self, content: str) -> str:
        """
        Normalize whitespace in content.
        
        Args:
            content: Text content
            
        Returns:
            Content with normalized whitespace
        """
        if not self.normalize_whitespace:
            return content
        
        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)
        
        # Replace multiple newlines with single newline (preserve some structure)
        if self.preserve_structure:
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        else:
            content = re.sub(r'\n+', ' ', content)
        
        # Remove leading/trailing whitespace from lines
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        
        return '\n'.join(lines)
    
    def filter_lines(self, content: str) -> str:
        """
        Filter lines based on length and content.
        
        Args:
            content: Text content
            
        Returns:
            Filtered content
        """
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip lines that are too short
            if len(line.strip()) < self.min_line_length:
                continue
            
            # Truncate lines that are too long
            if len(line) > self.max_line_length:
                line = line[:self.max_line_length] + "..."
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def preprocess(
        self,
        content: str,
        file_name: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Preprocess text content.
        
        Args:
            content: Text content to preprocess
            file_name: Name of the file
            language: Programming language (detected if not provided)
            
        Returns:
            Dictionary with preprocessed content and metadata
        """
        start_time = time.time()
        
        # Detect language if not provided
        if language is None:
            language = self.detect_language(content, file_name)
        
        original_length = len(content)
        original_lines = len(content.split('\n'))
        
        processed_content = content
        
        # Remove comments if requested
        if self.remove_comments:
            processed_content = self.remove_comments_from_content(processed_content, language)
        
        # Normalize whitespace
        processed_content = self.normalize_whitespace_content(processed_content)
        
        # Filter lines
        processed_content = self.filter_lines(processed_content)
        
        # Final cleanup
        processed_content = processed_content.strip()
        
        processed_length = len(processed_content)
        processed_lines = len(processed_content.split('\n')) if processed_content else 0
        
        elapsed_time = time.time() - start_time
        
        result = {
            'content': processed_content,
            'language': language,
            'original_length': original_length,
            'processed_length': processed_length,
            'original_lines': original_lines,
            'processed_lines': processed_lines,
            'compression_ratio': processed_length / original_length if original_length > 0 else 1.0,
            'processing_time_ms': int(elapsed_time * 1000),
            'settings': {
                'remove_comments': self.remove_comments,
                'normalize_whitespace': self.normalize_whitespace,
                'min_line_length': self.min_line_length,
                'max_line_length': self.max_line_length,
                'preserve_structure': self.preserve_structure
            }
        }
        
        logger.debug(f"Preprocessed '{file_name}' ({language}): {original_lines} -> {processed_lines} lines, "
                    f"{original_length} -> {processed_length} chars in {elapsed_time:.3f}s")
        
        return result
    
    def extract_meaningful_content(
        self,
        content: str,
        file_name: str,
        language: Optional[str] = None
    ) -> str:
        """
        Extract only meaningful content for embedding.
        
        Args:
            content: Text content
            file_name: Name of the file
            language: Programming language
            
        Returns:
            Meaningful content for embedding
        """
        # For code files, focus on function/class definitions and docstrings
        if language in ['python', 'javascript']:
            # Extract function/class definitions
            if language == 'python':
                patterns = [
                    r'(def\s+\w+\s*\([^)]*\)\s*:.*?(?=\ndef|\nclass|\Z))',
                    r'(class\s+\w+\s*\([^)]*\)\s*:.*?(?=\ndef|\nclass|\Z))',
                ]
            else:  # javascript
                patterns = [
                    r'(function\s+\w+\s*\([^)]*\)\s*{.*?})',
                    r'(const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{.*?})',
                    r'(class\s+\w+\s*{.*?})',
                ]
            
            meaningful_parts = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                meaningful_parts.extend(matches)
            
            if meaningful_parts:
                return '\n\n'.join(meaningful_parts)
        
        # For SQL, focus on table definitions and queries
        if language == 'sql':
            patterns = [
                r'(CREATE\s+TABLE\s+.*?;)',
                r'(SELECT\s+.*?;)',
                r'(INSERT\s+INTO\s+.*?;)',
                r'(UPDATE\s+.*?;)',
                r'(DELETE\s+FROM\s+.*?;)',
            ]
            
            meaningful_parts = []
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                meaningful_parts.extend(matches)
            
            if meaningful_parts:
                return '\n\n'.join(meaningful_parts)
        
        # For general text, return as-is after preprocessing
        return content