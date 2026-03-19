import re
import os
from typing import Optional, Tuple
from urllib.parse import urlparse


class RepoService:
    """
    Service for repository validation and management
    """
    
    @staticmethod
    def validate_github_url(repo_url: str) -> bool:
        """
        Validate if the provided URL is a valid GitHub repository URL
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not repo_url:
            return False
        
        # Remove trailing slashes and whitespace
        repo_url = repo_url.strip().rstrip('/')
        
        # Check if it contains github.com
        if 'github.com' not in repo_url.lower():
            return False
        
        # Pattern to match GitHub URLs
        # Supports: https://github.com/user/repo or git@github.com:user/repo.git
        patterns = [
            r'^https?://github\.com/[\w-]+/[\w.-]+/?$',
            r'^git@github\.com:[\w-]+/[\w.-]+\.git$',
        ]
        
        return any(re.match(pattern, repo_url, re.IGNORECASE) for pattern in patterns)
    
    @staticmethod
    def extract_repo_name(repo_url: str) -> Optional[str]:
        """
        Extract repository name from GitHub URL
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Repository name or None if extraction fails
            
        Examples:
            'https://github.com/user/my-repo' -> 'my-repo'
            'https://github.com/user/my-repo.git' -> 'my-repo'
        """
        if not repo_url:
            return None
        
        repo_url = repo_url.strip().rstrip('/')
        
        # Handle HTTPS URLs
        if repo_url.startswith('http'):
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) >= 2:
                repo_name = path_parts[1]
                # Remove .git suffix if present
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                return repo_name
        
        # Handle SSH URLs (git@github.com:user/repo.git)
        elif repo_url.startswith('git@'):
            match = re.search(r':[\w-]+/([\w.-]+)', repo_url)
            if match:
                repo_name = match.group(1)
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                return repo_name
        
        return None
    
    @staticmethod
    def normalize_github_url(repo_url: str) -> str:
        """
        Normalize GitHub URL to HTTPS format
        
        Args:
            repo_url: GitHub repository URL in any format
            
        Returns:
            Normalized HTTPS URL
        """
        repo_url = repo_url.strip().rstrip('/')
        
        # If it's already HTTPS, just clean it
        if repo_url.startswith('http'):
            # Remove .git suffix if present
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            return repo_url
        
        # Convert SSH to HTTPS
        if repo_url.startswith('git@github.com:'):
            # git@github.com:user/repo.git -> https://github.com/user/repo
            repo_path = repo_url.replace('git@github.com:', '')
            if repo_path.endswith('.git'):
                repo_path = repo_path[:-4]
            return f"https://github.com/{repo_path}"
        
        return repo_url
    
    @staticmethod
    def prepare_repository_directory(repo_name: str) -> str:
        """
        Prepare directory path for repository storage
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Directory path where repository will be stored
        """
        # Create base directory for repositories if it doesn't exist
        base_dir = os.path.join(os.getcwd(), 'repositories')
        os.makedirs(base_dir, exist_ok=True)
        
        # Create directory for this specific repository
        repo_dir = os.path.join(base_dir, repo_name)
        
        return repo_dir
    
    @staticmethod
    def save_zip_file(file_content: bytes, filename: str) -> str:
        """
        Save uploaded ZIP file to temporary storage
        
        Args:
            file_content: Binary content of the ZIP file
            filename: Original filename
            
        Returns:
            Path where file was saved
        """
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename to avoid collisions
        import time
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(temp_dir, safe_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
