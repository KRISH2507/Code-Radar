# 🔐 CORS & Authentication Guide

## Table of Contents
- [Understanding CORS](#understanding-cors)
- [The CORS Error Explained](#the-cors-error-explained)
- [Backend Setup (FastAPI)](#backend-setup-fastapi)
- [Frontend Setup (Next.js)](#frontend-setup-nextjs)
- [Google OAuth Configuration](#google-oauth-configuration)
- [Testing & Debugging](#testing--debugging)
- [Production Checklist](#production-checklist)

---

## Understanding CORS

### What is CORS?
**CORS (Cross-Origin Resource Sharing)** is a security mechanism that controls how web pages from one origin can request resources from another origin.

**Origin** = Protocol + Domain + Port
- `http://localhost:3000` (Frontend)
- `http://localhost:8000` (Backend)
→ These are **different origins** (different ports)

### Why Does CORS Exist?
Without CORS, malicious websites could steal your data by making requests to APIs while you're logged in. CORS protects users by:
1. Blocking unauthorized cross-origin requests
2. Requiring explicit server permission
3. Preventing credential theft

---

## The CORS Error Explained

### Error You're Seeing:
```
Access to fetch at 'http://localhost:8000/api/auth/google'
from origin 'http://localhost:3000'
has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present.
```

### What This Means:
1. **Frontend** (localhost:3000) tries to fetch from **Backend** (localhost:8000)
2. **Browser** intercepts the request
3. **Browser** checks: "Does the backend allow requests from localhost:3000?"
4. **Backend** didn't send proper CORS headers
5. **Browser** blocks the request

### CORS Preflight (OPTIONS Request)
For requests with:
- Custom headers (like `Authorization`)
- Methods other than GET/POST
- Content-Type other than simple types

Browser sends a **preflight OPTIONS request** first:
```
OPTIONS /api/auth/google
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization,content-type
```

Server must respond:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: authorization, content-type
Access-Control-Allow-Credentials: true
```

---

## Backend Setup (FastAPI)

### ✅ Correct CORS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# PRODUCTION-READY CORS SETUP
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Dev: Next.js default
    "http://127.0.0.1:3000",      # Dev: localhost alternative
    "https://yourapp.com",         # Production
    "https://www.yourapp.com",     # Production www
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ⚠️ NEVER use ["*"] with credentials!
    allow_credentials=True,         # Required for cookies/JWT
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
    ],
    expose_headers=["Content-Length"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

### ❌ Common Mistakes

```python
# ❌ DON'T: Using wildcard with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Won't work with allow_credentials=True
    allow_credentials=True,        # Browser will reject this combination
)

# ❌ DON'T: Missing credentials flag
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    # Missing: allow_credentials=True
)

# ❌ DON'T: Wrong origin format
app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost:3000"],  # Missing protocol!
)
```

### Key Rules:
1. **Never use `allow_origins=["*"]` with `allow_credentials=True`** - Browser will reject it
2. **Always specify full origin** including protocol (`http://` or `https://`)
3. **Include port number** if not standard (80/443)
4. **Order matters** - Add CORS middleware BEFORE routes

---

## Frontend Setup (Next.js)

### ✅ Correct Fetch with Credentials

```typescript
// CORRECT: Include credentials for CORS
export async function fetchAPI<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem('access_token');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',  // ✅ CRITICAL for CORS!
    mode: 'cors',           // ✅ Explicit CORS mode
  });

  return response.json();
}
```

### ❌ Common Mistakes

```typescript
// ❌ DON'T: Missing credentials
await fetch(url, {
  headers: { 'Content-Type': 'application/json' },
  // Missing: credentials: 'include'
});

// ❌ DON'T: Using 'same-origin' for cross-origin requests
await fetch(url, {
  credentials: 'same-origin',  // Won't send credentials to different port
});

// ❌ DON'T: Wrong mode
await fetch(url, {
  mode: 'no-cors',  // Can't read response or send credentials
});
```

### Credentials Options:
- `'include'` - Always send cookies/credentials (use this for cross-origin with auth)
- `'same-origin'` - Only for same origin
- `'omit'` - Never send credentials

---

## Google OAuth Configuration

### Backend Setup

#### 1. Install Google Auth Library
```bash
pip install google-auth
```

#### 2. Set Environment Variables
```bash
# .env
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret-here
```

#### 3. Google OAuth Endpoint (FastAPI)
```python
from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

router = APIRouter()

@router.post("/auth/google")
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Verify Google ID token and create/login user
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured"
        )
    
    try:
        # Verify token with Google
        idinfo = id_token.verify_oauth2_token(
            payload.token,
            google_requests.Request(),
            client_id
        )
        
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        
        if not email or not idinfo.get("email_verified"):
            raise HTTPException(
                status_code=400,
                detail="Email not verified by Google"
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid Google token: {str(e)}"
        )
    
    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        user = User(
            email=email,
            name=name,
            auth_provider="google",
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token({"user_id": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
```

### Frontend Setup (Next.js + Google OAuth)

#### 1. Install Google Library
```bash
npm install @react-oauth/google
```

#### 2. Setup Google Provider
```tsx
// app/layout.tsx
import { GoogleOAuthProvider } from '@react-oauth/google';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
          {children}
        </GoogleOAuthProvider>
      </body>
    </html>
  );
}
```

#### 3. Google Login Button
```tsx
// components/GoogleLoginButton.tsx
'use client';

import { GoogleLogin } from '@react-oauth/google';
import { useRouter } from 'next/navigation';
import { googleAuth } from '@/lib/api';

export default function GoogleLoginButton() {
  const router = useRouter();

  const handleSuccess = async (credentialResponse: any) => {
    try {
      // Send Google token to your backend
      const { data, error } = await googleAuth(credentialResponse.credential);
      
      if (error) {
        console.error('Google auth failed:', error);
        return;
      }
      
      // Save JWT token
      localStorage.setItem('access_token', data.access_token);
      
      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      console.error('Google OAuth error:', err);
    }
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => console.error('Google Login Failed')}
      useOneTap={false}
      theme="outline"
      size="large"
    />
  );
}
```

#### 4. Environment Variables
```env
# .env.local
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Google Cloud Console Setup

1. **Go to**: https://console.cloud.google.com/
2. **Create Project** or select existing
3. **Navigate to**: APIs & Services → Credentials
4. **Create OAuth 2.0 Client ID**:
   - Application type: **Web application**
   - Name: Your app name
   
5. **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://127.0.0.1:3000
   https://yourapp.com (production)
   ```

6. **Authorized redirect URIs**:
   ```
   http://localhost:3000
   http://localhost:3000/login
   https://yourapp.com (production)
   ```

7. **Copy Client ID** and add to both:
   - Frontend: `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
   - Backend: `GOOGLE_CLIENT_ID`

---

## Testing & Debugging

### Test CORS is Working

#### From Browser Console (open localhost:3000):
```javascript
// Test basic fetch
fetch('http://localhost:8000/api/cors-test', {
  credentials: 'include',
  mode: 'cors'
})
  .then(r => r.json())
  .then(data => console.log('✅ CORS Working:', data))
  .catch(err => console.error('❌ CORS Failed:', err));

// Test with Authorization header
fetch('http://localhost:8000/api/auth/me', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  mode: 'cors'
})
  .then(r => r.json())
  .then(data => console.log('✅ Auth Working:', data))
  .catch(err => console.error('❌ Auth Failed:', err));
```

### Check Network Tab

1. Open **DevTools** → **Network** tab
2. Make a request to your API
3. Look for:
   - **OPTIONS request** (preflight) - should return 200
   - **Actual request** (POST/GET) - should return expected status
4. Check **Response Headers**:
   ```
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Credentials: true
   ```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No Access-Control-Allow-Origin header" | CORS not configured | Add CORSMiddleware to backend |
| "Credentials flag is true, but allowed origin is *" | Using wildcard with credentials | Use specific origins |
| "The value of the Access-Control-Allow-Origin header must not be *" | Same as above | Use specific origins |
| OPTIONS request fails | Preflight not handled | Ensure OPTIONS in allow_methods |
| "Network error" | Backend not running | Start backend server |
| "Failed to fetch" | Wrong URL | Check API_URL in frontend |

---

## Production Checklist

### Backend (FastAPI)

- [ ] **Environment-based origins**:
  ```python
  ALLOWED_ORIGINS = [
      "https://yourapp.com",
      "https://www.yourapp.com",
  ]
  if os.getenv("ENVIRONMENT") == "development":
      ALLOWED_ORIGINS.extend([
          "http://localhost:3000",
          "http://127.0.0.1:3000",
      ])
  ```

- [ ] **HTTPS in production**:
  ```python
  allow_origins=[
      "https://yourapp.com",  # ✅ HTTPS
      # "http://yourapp.com",  # ❌ Don't allow HTTP in prod
  ]
  ```

- [ ] **Secure cookies** (if using):
  ```python
  response.set_cookie(
      key="access_token",
      value=token,
      httponly=True,      # Prevent JavaScript access
      secure=True,         # HTTPS only
      samesite="lax",     # CSRF protection
  )
  ```

- [ ] **Rate limiting** on auth endpoints
- [ ] **CORS whitelist** validated from database/config
- [ ] **Remove debug endpoints** (`/api/cors-test`)

### Frontend (Next.js)

- [ ] **Environment variables**:
  ```env
  # .env.production
  NEXT_PUBLIC_API_URL=https://api.yourapp.com
  NEXT_PUBLIC_GOOGLE_CLIENT_ID=prod-client-id
  ```

- [ ] **Update Google OAuth**:
  - Add production URL to Authorized Origins
  - Add production redirect URIs
  - Use production Client ID

- [ ] **Error handling**:
  ```typescript
  try {
    const response = await fetchAPI('/api/auth/login', {...});
    if (response.error) {
      // Show user-friendly error
      toast.error(response.error);
    }
  } catch (error) {
    // Network error
    toast.error('Unable to connect to server');
  }
  ```

- [ ] **Token refresh** logic
- [ ] **Secure token storage** (consider httpOnly cookies)
- [ ] **HTTPS redirect** in production

### Google OAuth Production

- [ ] **Verify all authorized origins**:
  ```
  https://yourapp.com
  https://www.yourapp.com
  ```

- [ ] **Verify redirect URIs**:
  ```
  https://yourapp.com/login
  https://yourapp.com/auth/google/callback
  ```

- [ ] **Enable OAuth Consent Screen**
- [ ] **Request necessary scopes** (email, profile)
- [ ] **Test with real Google account**

---

## Quick Reference

### CORS Headers Explained

| Header | What It Does |
|--------|--------------|
| `Access-Control-Allow-Origin` | Which origins can access the resource |
| `Access-Control-Allow-Credentials` | Whether to include cookies/auth headers |
| `Access-Control-Allow-Methods` | Which HTTP methods are allowed |
| `Access-Control-Allow-Headers` | Which headers frontend can send |
| `Access-Control-Expose-Headers` | Which response headers frontend can read |
| `Access-Control-Max-Age` | How long to cache preflight response |

### Fetch Credentials Options

| Option | When to Use |
|--------|-------------|
| `'include'` | Cross-origin requests with auth (JWT, cookies) |
| `'same-origin'` | Only requests to same origin |
| `'omit'` | Never send credentials |

---

## Support

If you're still experiencing issues:

1. **Check browser console** for detailed error messages
2. **Check network tab** for request/response headers
3. **Verify backend is running** on correct port
4. **Test CORS endpoint**: `http://localhost:8000/api/cors-test`
5. **Check environment variables** are loaded correctly

---

## Resources

- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Docs](https://fastapi.tiangolo.com/tutorial/cors/)
- [Google OAuth Setup](https://developers.google.com/identity/protocols/oauth2)
- [Fetch API: credentials](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#sending_a_request_with_credentials_included)
