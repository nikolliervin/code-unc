"""File handling utilities for git operations."""

import logging
import mimetypes
from pathlib import Path
from typing import Optional, Dict, List


logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations and language detection."""
    
    # Language mapping based on file extensions
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.cc': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'config',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.rst': 'rst',
        '.txt': 'text',
        '.log': 'log',
        '.dockerfile': 'dockerfile',
        '.r': 'r',
        '.R': 'r',
        '.m': 'matlab',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.pl': 'perl',
        '.lua': 'lua',
        '.vim': 'vim',
        '.ex': 'elixir',
        '.exs': 'elixir',
        '.erl': 'erlang',
        '.hrl': 'erlang',
        '.clj': 'clojure',
        '.cljs': 'clojure',
        '.hs': 'haskell',
        '.elm': 'elm',
        '.dart': 'dart',
        '.groovy': 'groovy',
        '.gradle': 'gradle',
        '.mk': 'makefile',
        '.cmake': 'cmake',
    }
    
    # File patterns that are typically binary
    BINARY_PATTERNS = {
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico', '.webp',
        # Archives
        '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz',
        # Executables
        '.exe', '.dll', '.so', '.dylib', '.bin', '.app',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Media
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
        # Fonts
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        # Others
        '.class', '.jar', '.war', '.ear', '.pyc', '.pyo', '.o', '.obj',
    }
    
    def __init__(self):
        """Initialize file handler."""
        pass
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect programming language from file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected language or None
        """
        if not file_path:
            return None
        
        path = Path(file_path)
        
        # Check for special filenames
        filename = path.name.lower()
        if filename in ['dockerfile', 'makefile', 'gemfile', 'rakefile', 'vagrantfile']:
            return filename
        
        # Check by extension
        extension = path.suffix.lower()
        if extension in self.LANGUAGE_MAP:
            return self.LANGUAGE_MAP[extension]
        
        # Check for files without extension but with shebangs (would need file content)
        return None
    
    def is_likely_binary(self, file_path: str) -> bool:
        """
        Check if a file is likely to be binary based on extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if likely binary, False otherwise
        """
        if not file_path:
            return False
        
        extension = Path(file_path).suffix.lower()
        return extension in self.BINARY_PATTERNS
    
    def is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if text file, False otherwise
        """
        if self.is_likely_binary(file_path):
            return False
        
        # Use mimetypes to check
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type.startswith('text/') or mime_type in [
                'application/json',
                'application/xml',
                'application/javascript',
                'application/x-python',
                'application/x-sh',
            ]
        
        # Default to True for unknown types (better to process than skip)
        return True
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes or None if error
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return None
    
    def should_review_file(
        self,
        file_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_size_kb: int = 500,
    ) -> bool:
        """
        Check if a file should be included in review.
        
        Args:
            file_path: Path to the file
            include_patterns: Patterns to include
            exclude_patterns: Patterns to exclude
            max_size_kb: Maximum file size in KB
            
        Returns:
            True if file should be reviewed
        """
        if not file_path:
            return False
        
        # Check if it's a text file
        if not self.is_text_file(file_path):
            return False
        
        # Check file size
        file_size = self.get_file_size(file_path)
        if file_size and file_size > max_size_kb * 1024:
            logger.debug(f"Skipping {file_path}: too large ({file_size} bytes)")
            return False
        
        # Apply pattern filtering
        import fnmatch
        
        # Check exclude patterns first
        if exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return False
        
        # Check include patterns
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return True
            return False  # No include pattern matched
        
        return True  # No patterns specified, include by default
    
    def get_file_info(self, file_path: str) -> Dict[str, Optional[str]]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        
        return {
            'name': path.name,
            'extension': path.suffix.lower(),
            'language': self.detect_language(file_path),
            'is_binary': self.is_likely_binary(file_path),
            'is_text': self.is_text_file(file_path),
            'size_bytes': self.get_file_size(file_path),
            'mime_type': mimetypes.guess_type(file_path)[0],
        }
    
    def get_common_languages(self, file_paths: List[str]) -> Dict[str, int]:
        """
        Get count of common languages in a list of files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping languages to counts
        """
        language_counts = {}
        
        for file_path in file_paths:
            language = self.detect_language(file_path)
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
        
        return dict(sorted(language_counts.items(), key=lambda x: x[1], reverse=True))
    
    def filter_reviewable_files(
        self,
        file_paths: List[str],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_files: int = 50,
        max_size_kb: int = 500,
    ) -> List[str]:
        """
        Filter a list of files to only include reviewable ones.
        
        Args:
            file_paths: List of file paths
            include_patterns: Patterns to include
            exclude_patterns: Patterns to exclude
            max_files: Maximum number of files to return
            max_size_kb: Maximum file size in KB
            
        Returns:
            Filtered list of file paths
        """
        reviewable_files = []
        
        for file_path in file_paths:
            if len(reviewable_files) >= max_files:
                break
            
            if self.should_review_file(
                file_path, include_patterns, exclude_patterns, max_size_kb
            ):
                reviewable_files.append(file_path)
        
        return reviewable_files 