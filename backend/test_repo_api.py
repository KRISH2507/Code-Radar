"""
Repository Ingestion API - Testing Examples

These examples show how to use the repository ingestion endpoints.
"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# 1. First, login to get a token
def login_and_get_token(email: str, password: str) -> str:
    """Login and retrieve JWT token"""
    
    # Step 1: Login to get OTP sent
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    print(f"Login response: {login_response.json()}")
    
    # Step 2: Verify OTP (you'll need to get the code from email)
    otp_code = input("Enter OTP code from email: ")
    
    verify_response = requests.post(
        f"{BASE_URL}/auth/verify-otp",
        json={"email": email, "code": otp_code}
    )
    
    token_data = verify_response.json()
    access_token = token_data["access_token"]
    print(f"Access token obtained: {access_token[:20]}...")
    
    return access_token


# 2. Submit a GitHub repository
def submit_github_repo(token: str, repo_url: str):
    """Submit a GitHub repository for scanning"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/repo/github",
        headers=headers,
        json={"repo_url": repo_url}
    )
    
    if response.status_code == 201:
        repo_data = response.json()
        print("\n✅ Repository created successfully!")
        print(f"Repository ID: {repo_data['id']}")
        print(f"Name: {repo_data['name']}")
        print(f"Status: {repo_data['status']}")
        print(f"Created at: {repo_data['created_at']}")
        return repo_data
    else:
        print(f"\n❌ Error: {response.json()}")
        return None


# 3. Upload a ZIP file
def upload_zip_file(token: str, file_path: str):
    """Upload a ZIP file containing source code"""
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.split('/')[-1], f, 'application/zip')}
        
        response = requests.post(
            f"{BASE_URL}/repo/zip",
            headers=headers,
            files=files
        )
    
    if response.status_code == 201:
        repo_data = response.json()
        print("\n✅ ZIP file uploaded successfully!")
        print(f"Repository ID: {repo_data['id']}")
        print(f"Name: {repo_data['name']}")
        print(f"Status: {repo_data['status']}")
        return repo_data
    else:
        print(f"\n❌ Error: {response.json()}")
        return None


# 4. Get all repositories
def get_repositories(token: str):
    """Get all repositories for the current user"""
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/repo",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📁 Total repositories: {data['total']}")
        
        for repo in data['repositories']:
            print(f"\n  - {repo['name']}")
            print(f"    ID: {repo['id']}")
            print(f"    Type: {repo['source_type']}")
            print(f"    Status: {repo['status']}")
            print(f"    URL: {repo.get('repo_url', 'N/A')}")
        
        return data
    else:
        print(f"\n❌ Error: {response.json()}")
        return None


# 5. Get a specific repository
def get_repository(token: str, repo_id: int):
    """Get a specific repository by ID"""
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/repo/{repo_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        repo = response.json()
        print(f"\n📦 Repository Details:")
        print(f"  Name: {repo['name']}")
        print(f"  Type: {repo['source_type']}")
        print(f"  Status: {repo['status']}")
        print(f"  URL: {repo.get('repo_url', 'N/A')}")
        return repo
    else:
        print(f"\n❌ Error: {response.json()}")
        return None


# 6. Delete a repository
def delete_repository(token: str, repo_id: int):
    """Delete a repository"""
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.delete(
        f"{BASE_URL}/repo/{repo_id}",
        headers=headers
    )
    
    if response.status_code == 204:
        print(f"\n✅ Repository {repo_id} deleted successfully!")
        return True
    else:
        print(f"\n❌ Error: {response.json()}")
        return False


# Example usage
if __name__ == "__main__":
    print("🚀 Code Radar - Repository Ingestion API Testing\n")
    
    # Example credentials (replace with your test account)
    EMAIL = "test@example.com"
    PASSWORD = "your_password"
    
    # Login and get token
    # token = login_and_get_token(EMAIL, PASSWORD)
    
    # Or use an existing token
    token = input("Enter your access token: ")
    
    print("\n" + "="*60)
    print("Testing Repository Endpoints")
    print("="*60)
    
    # Test 1: Submit GitHub repository
    print("\n1️⃣  Testing GitHub repository submission...")
    submit_github_repo(token, "https://github.com/facebook/react")
    
    # Test 2: Get all repositories
    print("\n2️⃣  Testing repository listing...")
    get_repositories(token)
    
    # Test 3: Get specific repository
    print("\n3️⃣  Testing get specific repository...")
    repo_id = int(input("\nEnter repository ID to fetch: "))
    get_repository(token, repo_id)
    
    # Test 4: Delete repository (optional)
    # delete_test = input("\nDo you want to test delete? (y/n): ")
    # if delete_test.lower() == 'y':
    #     repo_id = int(input("Enter repository ID to delete: "))
    #     delete_repository(token, repo_id)
    
    print("\n✨ Testing complete!")
