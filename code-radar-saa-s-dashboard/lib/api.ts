// API utility for making HTTP requests to the FastAPI backend
import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
}

// Create Axios instance with default configuration
const axiosInstance: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies and credentials
});

// Request interceptor: Attach JWT token to every request
axiosInstance.interceptors.request.use(
  (config) => {
    // Only access localStorage on client-side (Next.js SSR safety)
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 errors globally
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle 401 Unauthorized - clear token and redirect to login
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        console.log('[AUTH] 401 Unauthorized - clearing token and redirecting to login');
        localStorage.removeItem('access_token');
        localStorage.removeItem('pendingEmail');
        localStorage.removeItem('authMethod');
        localStorage.removeItem('pendingName');

        // Only redirect if not already on login/signup page
        if (!window.location.pathname.startsWith('/login') &&
          !window.location.pathname.startsWith('/signup') &&
          !window.location.pathname.startsWith('/otp')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Wrapper function to handle Axios responses and errors
 */
async function handleRequest<T = any>(
  request: Promise<AxiosResponse<T>>
): Promise<ApiResponse<T>> {
  try {
    const response = await request;
    return { data: response.data };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<any>;
      return {
        error: axiosError.response?.data?.detail ||
          axiosError.response?.data?.message ||
          axiosError.message ||
          'An error occurred',
      };
    }
    return {
      error: error instanceof Error ? error.message : 'Network error occurred',
    };
  }
}

/**
 * Sign up with email and password
 */
export async function signup(email: string, password: string, name?: string) {
  return handleRequest(
    axiosInstance.post('/auth/signup', { email, password, name })
  );
}

/**
 * Login with email and password
 */
export async function login(email: string, password: string) {
  return handleRequest(
    axiosInstance.post('/auth/login', { email, password })
  );
}

/**
 * Verify OTP code
 */
export async function verifyOTP(email: string, code: string) {
  return handleRequest<{ access_token: string; token_type: string }>(
    axiosInstance.post('/auth/verify-otp', { email, code })
  );
}

/**
 * Google OAuth authentication
 */
export async function googleAuth(token: string) {
  return handleRequest<{ access_token: string; token_type: string }>(
    axiosInstance.post('/auth/google', { token })
  );
}

/**
 * Resend OTP code to user's email
 */
export async function resendOTP(email: string) {
  return handleRequest(
    axiosInstance.post('/auth/resend-otp', { email })
  );
}

/**
 * Get current user info
 */
export async function getCurrentUser() {
  return handleRequest<{
    id: number
    email: string
    name: string | null
    is_verified: boolean
    plan: 'free' | 'pro'
    role: 'admin' | 'user'
    scan_count: number
    scan_reset_date: string | null
  }>(
    axiosInstance.get('/auth/me')
  )
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
}

/**
 * Logout user
 */
export function logout() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('pendingEmail');
  localStorage.removeItem('authMethod');
  localStorage.removeItem('pendingName');
  window.location.href = '/login';
}

/**
 * Get authentication token
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

// ============================================================================
// REPOSITORY API FUNCTIONS
// ============================================================================

/**
 * Submit a GitHub repository for scanning
 */
export async function submitGitHubRepo(repoUrl: string) {
  return handleRequest(
    axiosInstance.post('/repo/github', { repo_url: repoUrl })
  );
}

/**
 * Upload a ZIP file for scanning
 */
export async function uploadZipFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axiosInstance.post('/repo/zip', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { data: response.data };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<any>;
      return {
        error: axiosError.response?.data?.detail ||
          axiosError.response?.data?.message ||
          'Failed to upload file',
      };
    }
    return {
      error: error instanceof Error ? error.message : 'Network error occurred',
    };
  }
}

/**
 * Get all repositories for the current user
 */
export async function getUserRepositories(skip: number = 0, limit: number = 100) {
  return handleRequest(
    axiosInstance.get(`/repo?skip=${skip}&limit=${limit}`)
  );
}

/**
 * Get a specific repository by ID
 */
export async function getRepository(repositoryId: number) {
  return handleRequest(
    axiosInstance.get(`/repo/${repositoryId}`)
  );
}

/**
 * Delete a repository
 */
export async function deleteRepository(repositoryId: number) {
  return handleRequest(
    axiosInstance.delete(`/repo/${repositoryId}`)
  );
}

/**
 * Get repository scan status
 */
export async function getRepositoryStatus(repositoryId: number) {
  return handleRequest(
    axiosInstance.get(`/repo/${repositoryId}/status`)
  );
}

/**
 * Trigger a new scan for a repository
 */
export async function runScan(repositoryId: number) {
  console.log(`[API] Triggering scan for repository ID: ${repositoryId}`);

  const result = await handleRequest(
    axiosInstance.post(`/repo/${repositoryId}/scan`)
  );

  console.log(`[API] Scan trigger response:`, result);
  return result;
}

// ============================================================================
// DASHBOARD API FUNCTIONS
// ============================================================================

export interface DashboardStats {
  total_repositories: number
  completed_scans: number
  scanning_repos: number
  failed_scans: number
  total_files: number
  total_lines: number
  avg_health_score: number
  total_critical: number
  total_high: number
  total_medium: number
  total_low: number
  total_info: number
  total_issues: number
}

export interface OverviewRepo {
  id: number
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  source_type: string
  file_count: number | null
  line_count: number | null
  health_score: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  latest_scan_id: number | null
  created_at: string | null
  completed_at: string | null
}

/**
 * Get health score trend for a repository (from analysis routes).
 */
export async function getRepositoryTrend(repositoryId: number, limit: number = 8) {
  return handleRequest<{
    repository_id: number
    scan_count: number
    trend: Array<{
      scan_id: number
      created_at: string
      health_score: number
      critical_count: number
      high_count: number
      total_files: number
    }>
  }>(axiosInstance.get(`/analysis/repositories/${repositoryId}/trend?limit=${limit}`))
}

export async function getDashboardStats() {
  return handleRequest<DashboardStats>(
    axiosInstance.get('/dashboard/stats')
  )
}

/**
 * Get recent repositories with their latest scan health data.
 */
export async function getDashboardOverview() {
  return handleRequest<{ recent_repositories: OverviewRepo[] }>(
    axiosInstance.get('/dashboard/overview')
  )
}

// ============================================================================
// PAYMENTS API
// ============================================================================

export interface CreateOrderData {
  order_id: string
  amount: number
  currency: string
  key_id: string
}

/**
 * Create a Razorpay order for Pro upgrade
 */
export async function createOrder() {
  return handleRequest<CreateOrderData>(
    axiosInstance.post('/payments/create-order')
  )
}

/**
 * Verify Razorpay payment signature and upgrade user
 */
export async function verifyPayment(payload: {
  razorpay_order_id: string
  razorpay_payment_id: string
  razorpay_signature: string
}) {
  return handleRequest(axiosInstance.post('/payments/verify', payload))
}

// ============================================================================
// ADMIN API
// ============================================================================

export interface AdminUser {
  id: number
  email: string
  name: string | null
  plan: 'free' | 'pro'
  role: 'admin' | 'user'
  scan_count: number
  is_verified: boolean
}

/**
 * List all users (admin only)
 */
export async function getAdminUsers(page = 1, pageSize = 50) {
  return handleRequest<{ users: AdminUser[]; total: number }>(
    axiosInstance.get(`/admin/users?page=${page}&page_size=${pageSize}`)
  )
}

/**
 * Manually change a user's plan (admin only)
 */
export async function updateUserPlan(userId: number, plan: 'free' | 'pro') {
  return handleRequest(axiosInstance.patch(`/admin/users/${userId}/plan`, { plan }))
}
