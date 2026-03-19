# Repository Ingestion API

This module provides repository ingestion functionality for the Code Radar SaaS platform.

## Features

✅ **GitHub Repository Ingestion**
- Submit GitHub repository URLs
- Automatic URL validation and normalization
- Extract repository name from URL
- Store repository metadata

✅ **ZIP File Upload**
- Upload ZIP files containing source code
- Size validation (max 100MB)
- Temporary file storage
- Extract name from filename

✅ **Repository Management**
- List all repositories for authenticated user
- Get specific repository details
- Delete repositories
- Pagination support

✅ **Security**
- JWT authentication on all endpoints
- User isolation (users can only see their own repos)
- Input validation

## Database Models

### Repository
```python
- id: Primary key
- user_id: Foreign key to users table
- name: Repository name
- source_type: "github" or "zip"
- repo_url: GitHub URL or file path
- status: "pending", "processing", "completed", "failed"
- created_at: Timestamp
- updated_at: Timestamp
```

### Scan
```python
- id: Primary key
- repository_id: Foreign key to repositories
- status: "pending", "running", "completed", "failed"
- started_at: Timestamp
- completed_at: Timestamp
- created_at: Timestamp
```

## API Endpoints

### 1. Submit GitHub Repository
```http
POST /repo/github
Authorization: Bearer <token>
Content-Type: application/json

{
  "repo_url": "https://github.com/user/repo"
}
```

**Response (201):**
```json
{
  "id": 1,
  "user_id": 5,
  "name": "repo",
  "source_type": "github",
  "repo_url": "https://github.com/user/repo",
  "status": "pending",
  "created_at": "2026-02-06T10:30:00Z"
}
```

### 2. Upload ZIP File
```http
POST /repo/zip
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary ZIP file>
```

**Response (201):**
```json
{
  "id": 2,
  "user_id": 5,
  "name": "my-project",
  "source_type": "zip",
  "repo_url": "/path/to/file.zip",
  "status": "pending",
  "created_at": "2026-02-06T10:35:00Z"
}
```

### 3. List Repositories
```http
GET /repo?skip=0&limit=100
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "repositories": [
    {
      "id": 1,
      "user_id": 5,
      "name": "repo",
      "source_type": "github",
      "repo_url": "https://github.com/user/repo",
      "status": "pending",
      "created_at": "2026-02-06T10:30:00Z"
    }
  ],
  "total": 1
}
```

### 4. Get Specific Repository
```http
GET /repo/{repository_id}
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 1,
  "user_id": 5,
  "name": "repo",
  "source_type": "github",
  "repo_url": "https://github.com/user/repo",
  "status": "pending",
  "created_at": "2026-02-06T10:30:00Z"
}
```

### 5. Delete Repository
```http
DELETE /repo/{repository_id}
Authorization: Bearer <token>
```

**Response (204 No Content)**

## Service Layer

### RepoService

The `RepoService` class provides business logic for repository operations:

**Methods:**
- `validate_github_url(repo_url)` - Validate GitHub URL format
- `extract_repo_name(repo_url)` - Extract repository name from URL
- `normalize_github_url(repo_url)` - Convert any GitHub URL format to HTTPS
- `prepare_repository_directory(repo_name)` - Prepare storage directory
- `save_zip_file(file_content, filename)` - Save uploaded ZIP file

## Usage Example

### Frontend Integration (React/TypeScript)

```typescript
import { fetchAPI } from '@/lib/api'

// Submit GitHub repository
async function submitGitHubRepo(repoUrl: string) {
  const { data, error } = await fetchAPI('/repo/github', {
    method: 'POST',
    body: JSON.stringify({ repo_url: repoUrl })
  })
  
  if (error) {
    console.error('Failed to submit repository:', error)
    return null
  }
  
  return data
}

// Upload ZIP file
async function uploadZipFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  const token = localStorage.getItem('access_token')
  
  const response = await fetch('http://localhost:8000/repo/zip', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  })
  
  return await response.json()
}

// Get repositories
async function getRepositories() {
  const { data, error } = await fetchAPI('/repo')
  
  if (error) {
    console.error('Failed to fetch repositories:', error)
    return []
  }
  
  return data.repositories
}
```

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"
token = "your_jwt_token"

# Submit GitHub repository
response = requests.post(
    f"{BASE_URL}/repo/github",
    headers={"Authorization": f"Bearer {token}"},
    json={"repo_url": "https://github.com/facebook/react"}
)
repo = response.json()
print(f"Created repository: {repo['name']} (ID: {repo['id']})")

# List repositories
response = requests.get(
    f"{BASE_URL}/repo",
    headers={"Authorization": f"Bearer {token}"}
)
repos = response.json()
print(f"Total repositories: {repos['total']}")
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request` - Invalid input (bad URL, non-ZIP file, etc.)
- `401 Unauthorized` - Missing or invalid JWT token
- `404 Not Found` - Repository doesn't exist or doesn't belong to user
- `409 Conflict` - Repository already exists
- `413 Payload Too Large` - ZIP file exceeds 100MB limit

## Next Steps

The following features will be added in future iterations:

- [ ] Actual repository cloning (currently only metadata is stored)
- [ ] Code scanning and analysis
- [ ] Scan result storage and retrieval
- [ ] Background job processing with Celery
- [ ] Webhook support for GitHub repositories
- [ ] Repository synchronization
- [ ] Advanced search and filtering

## File Structure

```
backend/app/
├── models/
│   ├── repository.py        # Repository model
│   └── scan.py              # Scan model
├── schemas/
│   └── repo.py              # Pydantic schemas
├── services/
│   └── repo_service.py      # Business logic
├── api/
│   └── repo.py              # API routes
└── core/
    └── jwt.py               # JWT auth with get_current_user
```

## Testing

Run the test script:

```bash
cd backend
python test_repo_api.py
```

Or use the interactive API documentation:

```
http://localhost:8000/docs
```

## Notes

- Repository cloning is not implemented yet - only metadata is stored
- Scanning is not implemented yet - status will remain "pending"
- ZIP files are stored in `temp_uploads/` directory
- Repository directories will be created in `repositories/` directory
