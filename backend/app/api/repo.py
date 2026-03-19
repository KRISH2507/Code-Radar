import threading
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import get_current_user
from app.models.user import User
from app.models.repository import Repository, SourceType, RepositoryStatus
from app.schemas.repo import (
    GitHubRepoRequest,
    RepositoryResponse,
    RepositoryListResponse
)
from app.services.repo_service import RepoService
from app.services.plan_service import check_and_increment_scan

router = APIRouter()
repo_service = RepoService()


def _dispatch_scan(repository_id: int) -> None:
    """
    Dispatch a scan task. Tries Celery first; if Redis is unavailable,
    falls back to running the scan in a daemon thread so the HTTP
    response is never blocked.
    """
    from app.workers.scan_worker import scan_repository, _scan_repository_impl
    try:
        scan_repository.delay(repository_id)
        print(f"[SCAN DISPATCH] Enqueued Celery task for repo {repository_id}")
    except Exception as e:
        print(f"[SCAN DISPATCH] Celery unavailable ({e}), running scan in background thread")
        t = threading.Thread(
            target=_scan_repository_impl,
            args=(repository_id,),
            daemon=True,
        )
        t.start()


@router.post(
    "/github",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a GitHub repository for scanning"
)
def create_github_repository(
    payload: GitHubRepoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a GitHub repository URL for analysis.
    
    - **repo_url**: Full GitHub repository URL (e.g., https://github.com/user/repo)
    
    Returns the created repository with ID and status.
    """
    # Validate GitHub URL
    if not repo_service.validate_github_url(payload.repo_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL. Please provide a valid GitHub URL."
        )
    
    # Normalize URL
    normalized_url = repo_service.normalize_github_url(payload.repo_url)
    
    # Extract repository name
    repo_name = repo_service.extract_repo_name(normalized_url)
    if not repo_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract repository name from URL"
        )
    
    # Check if repository already exists for this user
    existing_repo = (
        db.query(Repository)
        .filter(
            Repository.user_id == current_user.id,
            Repository.repo_url == normalized_url
        )
        .first()
    )
    
    if existing_repo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This repository has already been added to your account"
        )
    
    # Create repository record
    repository = Repository(
        user_id=current_user.id,
        name=repo_name,
        source_type=SourceType.GITHUB,
        repo_url=normalized_url,
        status=RepositoryStatus.PENDING
    )
    
    db.add(repository)
    db.commit()
    db.refresh(repository)

    # Enforce scan limit BEFORE dispatching
    check_and_increment_scan(current_user, db)

    # Dispatch scan in background — response returns immediately
    background_tasks.add_task(_dispatch_scan, repository.id)

    return repository


@router.post(
    "/zip",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a ZIP file containing source code"
)
async def create_zip_repository(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="ZIP file containing the source code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a ZIP file containing source code for analysis.
    
    - **file**: ZIP file upload
    
    Returns the created repository with ID and status.
    """
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are supported"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Check file size (limit to 100MB)
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 100MB limit"
        )
    
    # Save file to temporary storage
    file_path = repo_service.save_zip_file(file_content, file.filename)
    
    # Extract name from filename (remove .zip extension)
    repo_name = file.filename[:-4] if file.filename.endswith('.zip') else file.filename
    
    # Create repository record
    repository = Repository(
        user_id=current_user.id,
        name=repo_name,
        source_type=SourceType.ZIP,
        repo_url=file_path,  # Store file path as repo_url
        status=RepositoryStatus.PENDING
    )
    
    db.add(repository)
    db.commit()
    db.refresh(repository)

    # Enforce scan limit BEFORE dispatching
    check_and_increment_scan(current_user, db)

    # Dispatch scan in background — response returns immediately
    background_tasks.add_task(_dispatch_scan, repository.id)

    return repository


@router.get(
    "",
    response_model=RepositoryListResponse,
    summary="Get all repositories for the current user"
)
def get_user_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all repositories belonging to the authenticated user.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    
    Returns a list of repositories with their metadata.
    """
    # Query repositories for current user
    repositories = (
        db.query(Repository)
        .filter(Repository.user_id == current_user.id)
        .order_by(Repository.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Get total count
    total = (
        db.query(Repository)
        .filter(Repository.user_id == current_user.id)
        .count()
    )
    
    return RepositoryListResponse(
        repositories=repositories,
        total=total
    )


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
    summary="Get a specific repository by ID"
)
def get_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific repository by its ID.
    
    Only returns the repository if it belongs to the authenticated user.
    """
    repository = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id,
            Repository.user_id == current_user.id
        )
        .first()
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repository


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a repository"
)
def delete_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a repository by its ID.
    
    Only allows deletion if the repository belongs to the authenticated user.
    """
    repository = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id,
            Repository.user_id == current_user.id
        )
        .first()
    )
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    db.delete(repository)
    db.commit()
    
    return None


@router.get(
    "/{repository_id}/status",
    summary="Poll repository + latest scan status",
)
def get_repository_scan_status(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Convenience alias — delegates to /api/analysis/repositories/{id}/status.
    Returns repository status + latest scan in one call.
    Poll this until latest_scan.status == 'completed' or 'failed'.
    """
    from sqlalchemy import desc
    from app.models.scan import Scan
    from app.schemas.scan import ScanResponse, RepositoryStatusResponse

    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id, Repository.user_id == current_user.id)
        .first()
    )
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    latest_scan = (
        db.query(Scan)
        .filter(Scan.repository_id == repository_id)
        .order_by(desc(Scan.created_at))
        .first()
    )

    return RepositoryStatusResponse(
        repository_id=repository.id,
        repository_status=repository.status.value,
        latest_scan=ScanResponse.model_validate(latest_scan) if latest_scan else None,
    )


@router.post(
    "/{repository_id}/scan",
    response_model=RepositoryResponse,
    summary="Trigger a new scan for a repository"
)
def trigger_repository_scan(
    repository_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger a new scan for an existing repository.
    
    This endpoint can be used to re-scan a repository that has already been added.
    
    - **repository_id**: ID of the repository to scan
    
    Returns the repository with updated status.
    """
    print(f"[SCAN API] Received request to scan repository ID: {repository_id}")
    
    # Check if repository exists and belongs to current user
    repository = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id,
            Repository.user_id == current_user.id
        )
        .first()
    )
    
    if not repository:
        print(f"[SCAN API] Repository {repository_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Check if repository is already being scanned
    if repository.status == RepositoryStatus.PROCESSING:
        print(f"[SCAN API] Repository {repository_id} is already being scanned")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository is already being scanned"
        )
    
    # Update status to PENDING
    repository.status = RepositoryStatus.PENDING
    db.commit()
    db.refresh(repository)

    print(f"[SCAN API] Updated repository {repository_id} status to PENDING")

    # Enforce scan limit BEFORE dispatching
    check_and_increment_scan(current_user, db)

    # Dispatch scan in background — response returns immediately
    background_tasks.add_task(_dispatch_scan, repository_id)

    print(f"[SCAN API] Scan dispatched for repository {repository_id}")
    return repository
