"""
File Scanner Service

Analyzes code files to extract metrics:
- Line counts
- File types distribution
- Code complexity (if available)
- Language detection

Production-ready with:
- Async file reading
- Memory-efficient streaming
- Error handling
- Progress tracking
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class FileScannerError(Exception):
    """Base exception for file scanner errors"""
    pass


class FileScanner:
    """
    Service for scanning and analyzing code files.
    
    Features:
    - Concurrent file reading
    - Language detection
    - Line counting
    - File type classification
    - Memory-efficient streaming
    """
    
    # Language mappings by file extension
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c': 'C',
        '.h': 'C/C++',
        '.hpp': 'C++',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sh': 'Shell',
        '.bash': 'Shell',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.md': 'Markdown',
        '.txt': 'Text',
    }
    
    # Binary/compiled file extensions to skip
    BINARY_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.exe', '.bin', '.jar', '.war', '.class',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp',
        '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
        '.mp4', '.mp3', '.wav', '.avi', '.mov',
        '.woff', '.woff2', '.ttf', '.eot', '.otf'
    }
    
    # Directories to exclude
    EXCLUDED_DIRS = {
        '.git', 'node_modules', '__pycache__', '.next',
        'dist', 'build', 'venv', '.venv', 'env',
        'target', 'bin', 'obj', '.idea', '.vscode',
        'coverage', '.pytest_cache', '.mypy_cache'
    }
    
    @classmethod
    async def scan_directory(
        cls,
        directory: str,
        max_concurrent: int = 50
    ) -> Dict[str, any]:
        """
        Scan a directory and collect file metrics.
        
        Args:
            directory: Path to directory to scan
            max_concurrent: Maximum concurrent file reads
            
        Returns:
            Dict containing scan results
        """
        if not os.path.exists(directory):
            raise FileScannerError(f"Directory not found: {directory}")
        
        if not os.path.isdir(directory):
            raise FileScannerError(f"Path is not a directory: {directory}")
        
        logger.info(f"Starting directory scan: {directory}")
        
        # Collect all files to scan
        files_to_scan = []
        for root, dirs, files in os.walk(directory):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in cls.EXCLUDED_DIRS]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                
                # Skip binary files
                if ext in cls.BINARY_EXTENSIONS:
                    continue
                
                files_to_scan.append(filepath)
        
        logger.info(f"Found {len(files_to_scan)} files to scan")
        
        # Scan files concurrently with semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = [
            cls._scan_file_with_semaphore(filepath, semaphore)
            for filepath in files_to_scan
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        total_lines = 0
        total_files = 0
        language_stats = defaultdict(lambda: {'files': 0, 'lines': 0})
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                continue
            
            if result is None:  # Skipped file
                continue
            
            total_lines += result['lines']
            total_files += 1
            
            language = result['language']
            language_stats[language]['files'] += 1
            language_stats[language]['lines'] += result['lines']
        
        logger.info(f"Scan complete: {total_files} files, {total_lines} lines")
        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'language_stats': dict(language_stats),
            'errors': errors,
            'directory': directory
        }
    
    @classmethod
    async def _scan_file_with_semaphore(
        cls,
        filepath: str,
        semaphore: asyncio.Semaphore
    ) -> Optional[Dict[str, any]]:
        """
        Scan a single file with semaphore for concurrency control.
        
        Args:
            filepath: Path to file
            semaphore: Semaphore for concurrency control
            
        Returns:
            File metrics or None if skipped
        """
        async with semaphore:
            return await cls._scan_file(filepath)
    
    @classmethod
    async def _scan_file(cls, filepath: str) -> Optional[Dict[str, any]]:
        """
        Scan a single file for metrics.
        
        Args:
            filepath: Path to file
            
        Returns:
            File metrics dict or None if skipped
        """
        try:
            # Get file extension and language
            ext = os.path.splitext(filepath)[1].lower()
            language = cls.LANGUAGE_MAP.get(ext, 'Other')
            
            # Read file and count lines asynchronously
            loop = asyncio.get_event_loop()
            line_count = await loop.run_in_executor(
                None,
                cls._count_lines_sync,
                filepath
            )
            
            if line_count is None:  # Binary or unreadable
                return None
            
            return {
                'filepath': filepath,
                'language': language,
                'lines': line_count,
                'extension': ext
            }
            
        except Exception as e:
            logger.warning(f"Error scanning {filepath}: {e}")
            return None
    
    @staticmethod
    def _count_lines_sync(filepath: str) -> Optional[int]:
        """
        Count lines in a file (synchronous).
        
        Args:
            filepath: Path to file
            
        Returns:
            Line count or None if unreadable
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except (IOError, OSError, UnicodeDecodeError):
            # Try binary read as fallback
            try:
                with open(filepath, 'rb') as f:
                    # If file is very large, it's probably binary
                    sample = f.read(512)
                    if b'\x00' in sample:  # Null bytes indicate binary
                        return None
                    
                    # Count lines in text mode
                    f.seek(0)
                    return sum(1 for _ in f)
            except Exception:
                return None
    
    @classmethod
    async def scan_single_file(cls, filepath: str) -> Optional[Dict[str, any]]:
        """
        Scan a single file for metrics.
        
        Args:
            filepath: Path to file
            
        Returns:
            File metrics or None if skipped
        """
        return await cls._scan_file(filepath)
    
    @classmethod
    def get_language_from_extension(cls, extension: str) -> str:
        """
        Get programming language from file extension.
        
        Args:
            extension: File extension (with or without dot)
            
        Returns:
            Language name or 'Other'
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        return cls.LANGUAGE_MAP.get(extension.lower(), 'Other')
    
    @classmethod
    def is_code_file(cls, filename: str) -> bool:
        """
        Check if a file is a code file.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if code file, False otherwise
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.LANGUAGE_MAP and ext not in cls.BINARY_EXTENSIONS
    
    @classmethod
    def format_scan_summary(cls, scan_results: Dict[str, any]) -> str:
        """
        Format scan results into a human-readable summary.
        
        Args:
            scan_results: Results from scan_directory()
            
        Returns:
            Formatted summary string
        """
        lines = [
            f"📊 Scan Summary",
            f"=" * 50,
            f"Total Files: {scan_results['total_files']:,}",
            f"Total Lines: {scan_results['total_lines']:,}",
            f"",
            f"Language Breakdown:",
            f"-" * 50
        ]
        
        # Sort languages by line count
        lang_stats = scan_results['language_stats']
        sorted_langs = sorted(
            lang_stats.items(),
            key=lambda x: x[1]['lines'],
            reverse=True
        )
        
        for language, stats in sorted_langs:
            percentage = (stats['lines'] / scan_results['total_lines'] * 100) if scan_results['total_lines'] > 0 else 0
            lines.append(
                f"  {language:15s} {stats['files']:5d} files  {stats['lines']:8,d} lines ({percentage:5.1f}%)"
            )
        
        if scan_results['errors']:
            lines.extend([
                f"",
                f"⚠️  Errors: {len(scan_results['errors'])}",
                f"-" * 50
            ])
        
        return "\n".join(lines)
