from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum


class SourceType(str, Enum):
    GITHUB = "github"
    ZIP = "zip"


class RepositoryStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GitHubRepoRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")

    @validator("repo_url")
    def validate_github_url(cls, v):
        if not v:
            raise ValueError("Repository URL is required")
        
        v = v.strip()
        
        # Basic validation - must contain github.com
        if "github.com" not in v.lower():
            raise ValueError("Must be a valid GitHub URL")
        
        return v


class RepositoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    source_type: SourceType
    repo_url: Optional[str]
    status: RepositoryStatus
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryResponse]
    total: int
