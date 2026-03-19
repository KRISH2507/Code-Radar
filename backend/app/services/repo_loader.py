"""
Repository Loader Service

Handles downloading and extracting repositories from various sources:
- GitHub repositories (via git clone)
- ZIP file uploads

Production-ready with:
- Async operations
- Size validation
- Security checks
- Error handling
- Resource cleanup
"""

import os
import tempfile
import shutil
import zipfile
import subprocess
import asyncio
from typing import Optional, Dict, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RepoLoaderError(Exception):
    """Base exception for repository loader errors"""
    pass


class RepositorySizeError(RepoLoaderError):
    """Raised when repository exceeds size limits"""
    pass


class RepositoryValidationError(RepoLoaderError):
    """Raised when repository validation fails"""
    pass


class RepoLoader:
    """
    Service for loading repositories from various sources.
    
    Features:
    - Git clone with shallow depth
    - ZIP file extraction with validation
    - Size limits and security checks
    - Automatic cleanup
    """
    
    # Configuration constants
    MAX_REPO_SIZE_MB = 500  # Maximum repository size in MB
    CLONE_TIMEOUT_SECONDS = 300  # 5 minutes
    CLONE_DEPTH = 1  # Shallow clone
    
    # Directories to exclude from scanning
    EXCLUDED_DIRS = {
        '.git', 'node_modules', '__pycache__', '.next', 
        'dist', 'build', 'venv', '.venv', 'env',
        'target', 'bin', 'obj', '.idea', '.vscode'
    }
    
    # File extensions to exclude
    EXCLUDED_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.exe', '.bin', '.jar', '.war', '.class',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
        '.pdf', '.zip', '.tar', '.gz', '.rar'
    }
    
    @classmethod
    async def clone_github_repo(
        cls,
        repo_url: str,
        destination: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Clone a GitHub repository with safety checks.
        
        Args:
            repo_url: GitHub repository URL (HTTPS format)
            destination: Optional path where to clone (creates temp dir if None)
            
        Returns:
            Dict containing repo_path and metadata
            
        Raises:
            RepositoryValidationError: If URL is invalid or unsafe
            RepositorySizeError: If repository is too large
            RepoLoaderError: For other errors
        """
        # Validate URL
        if not cls._validate_github_url(repo_url):
            raise RepositoryValidationError(f"Invalid GitHub URL: {repo_url}")
        
        # Create destination directory
        if destination is None:
            destination = tempfile.mkdtemp(prefix="coderadar_github_")
        else:
            os.makedirs(destination, exist_ok=True)
        
        logger.info(f"Cloning GitHub repository: {repo_url} to {destination}")
        
        try:
            # Run git clone asynchronously
            process = await asyncio.create_subprocess_exec(
                'git', 'clone',
                '--depth', str(cls.CLONE_DEPTH),
                '--single-branch',
                '--no-tags',
                repo_url,
                destination,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=cls.CLONE_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                process.kill()
                raise RepoLoaderError(f"Clone timed out after {cls.CLONE_TIMEOUT_SECONDS}s")
            
            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise RepoLoaderError(f"Git clone failed: {error_msg}")
            
            logger.info(f"Successfully cloned repository to {destination}")
            
            # Verify size
            size_mb = cls._get_directory_size_mb(destination)
            if size_mb > cls.MAX_REPO_SIZE_MB:
                shutil.rmtree(destination, ignore_errors=True)
                raise RepositorySizeError(
                    f"Repository size ({size_mb:.1f}MB) exceeds limit ({cls.MAX_REPO_SIZE_MB}MB)"
                )
            
            return {
                'repo_path': destination,
                'size_mb': size_mb,
                'source_type': 'github',
                'url': repo_url
            }
            
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(destination):
                shutil.rmtree(destination, ignore_errors=True)
            raise
    
    @classmethod
    async def extract_zip_file(
        cls,
        zip_path: str,
        destination: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Extract and validate a ZIP file.
        
        Args:
            zip_path: Path to ZIP file
            destination: Optional extraction path (creates temp dir if None)
            
        Returns:
            Dict containing extracted_path and metadata
            
        Raises:
            RepositoryValidationError: If ZIP is invalid or unsafe
            RepositorySizeError: If extracted size exceeds limit
            RepoLoaderError: For other errors
        """
        if not os.path.exists(zip_path):
            raise RepositoryValidationError(f"ZIP file not found: {zip_path}")
        
        # Create destination directory
        if destination is None:
            destination = tempfile.mkdtemp(prefix="coderadar_zip_")
        else:
            os.makedirs(destination, exist_ok=True)
        
        logger.info(f"Extracting ZIP file: {zip_path} to {destination}")
        
        try:
            # Validate ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Test ZIP integrity
                if zip_ref.testzip() is not None:
                    raise RepositoryValidationError("ZIP file is corrupted")
                
                # Check for zip bombs (excessive compression ratio)
                compressed_size = os.path.getsize(zip_path)
                uncompressed_size = sum(info.file_size for info in zip_ref.filelist)
                
                compression_ratio = uncompressed_size / compressed_size if compressed_size > 0 else 0
                if compression_ratio > 100:  # More than 100:1 is suspicious
                    raise RepositoryValidationError(
                        f"Suspicious ZIP file (compression ratio: {compression_ratio:.1f}:1)"
                    )
                
                # Check uncompressed size
                uncompressed_size_mb = uncompressed_size / (1024 * 1024)
                if uncompressed_size_mb > cls.MAX_REPO_SIZE_MB:
                    raise RepositorySizeError(
                        f"ZIP contents ({uncompressed_size_mb:.1f}MB) exceed limit ({cls.MAX_REPO_SIZE_MB}MB)"
                    )
                
                # Check for path traversal attacks
                for member in zip_ref.namelist():
                    if member.startswith('/') or '..' in member:
                        raise RepositoryValidationError(
                            f"Unsafe file path in ZIP: {member}"
                        )
                
                # Extract files (run in executor to avoid blocking)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, zip_ref.extractall, destination)
            
            logger.info(f"Successfully extracted ZIP to {destination}")
            
            # Verify actual size after extraction
            size_mb = cls._get_directory_size_mb(destination)
            
            return {
                'repo_path': destination,
                'size_mb': size_mb,
                'source_type': 'zip',
                'file_count': len(list(Path(destination).rglob('*'))),
                'original_zip': zip_path
            }
            
        except zipfile.BadZipFile:
            if os.path.exists(destination):
                shutil.rmtree(destination, ignore_errors=True)
            raise RepositoryValidationError("Invalid or corrupted ZIP file")
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(destination):
                shutil.rmtree(destination, ignore_errors=True)
            raise
    
    @classmethod
    def cleanup_repository(cls, repo_path: str) -> None:
        """
        Clean up a repository directory.
        
        Args:
            repo_path: Path to repository to delete
        """
        if os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info(f"Cleaned up repository: {repo_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup {repo_path}: {e}")
    
    @classmethod
    def _validate_github_url(cls, url: str) -> bool:
        """
        Validate GitHub URL for security.
        
        Args:
            url: GitHub URL to validate
            
        Returns:
            True if valid and safe, False otherwise
        """
        if not url:
            return False
        
        url = url.strip().lower()
        
        # Must be HTTPS (never SSH or git://)
        if not url.startswith('https://github.com/'):
            return False
        
        # Basic format check
        parts = url.replace('https://github.com/', '').rstrip('/').split('/')
        if len(parts) < 2:
            return False
        
        # Check for suspicious patterns
        dangerous_patterns = ['..', '~', '$', '`', ';', '|', '&']
        if any(pattern in url for pattern in dangerous_patterns):
            return False
        
        return True
    
    @classmethod
    def _get_directory_size_mb(cls, path: str) -> float:
        """
        Calculate directory size in megabytes.
        
        Args:
            path: Directory path
            
        Returns:
            Size in MB
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    continue
        
        return total_size / (1024 * 1024)
    
    @classmethod
    def should_exclude_directory(cls, dirname: str) -> bool:
        """Check if directory should be excluded from scanning."""
        return dirname in cls.EXCLUDED_DIRS
    
    @classmethod
    def should_exclude_file(cls, filename: str) -> bool:
        """Check if file should be excluded from scanning."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.EXCLUDED_EXTENSIONS
