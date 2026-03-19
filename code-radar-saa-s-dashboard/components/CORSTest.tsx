'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

/**
 * CORS Testing Component
 * Use this to verify your CORS configuration is working correctly
 * 
 * Add to any page: <CORSTest />
 */
export default function CORSTest() {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [details, setDetails] = useState<any>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const testCORS = async () => {
    setStatus('loading');
    setMessage('Testing CORS configuration...');
    setDetails(null);

    try {
      // Test 1: Basic CORS test
      const corsResponse = await fetch(`${API_URL}/api/cors-test`, {
        method: 'GET',
        credentials: 'include',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!corsResponse.ok) {
        throw new Error(`HTTP ${corsResponse.status}: ${corsResponse.statusText}`);
      }

      const corsData = await corsResponse.json();

      // Test 2: Check response headers
      const allowOrigin = corsResponse.headers.get('Access-Control-Allow-Origin');
      const allowCredentials = corsResponse.headers.get('Access-Control-Allow-Credentials');

      setStatus('success');
      setMessage('✅ CORS is configured correctly!');
      setDetails({
        ...corsData,
        headers: {
          'Access-Control-Allow-Origin': allowOrigin || 'Not set',
          'Access-Control-Allow-Credentials': allowCredentials || 'Not set',
        },
        frontend_origin: window.location.origin,
        backend_url: API_URL,
      });
    } catch (error) {
      setStatus('error');
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        setMessage('❌ CORS Error: Cannot connect to backend');
        setDetails({
          error: 'Failed to fetch',
          likely_causes: [
            'Backend server is not running',
            'CORS middleware not configured',
            'Wrong API URL',
            'Network connectivity issue',
          ],
          backend_url: API_URL,
          check: 'Is the backend running on ' + API_URL + '?',
        });
      } else {
        setMessage(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}');
        setDetails({
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }
  };

  const testAuth = async () => {
    setStatus('loading');
    setMessage('Testing authenticated endpoint...');
    setDetails(null);

    const token = localStorage.getItem('access_token');

    if (!token) {
      setStatus('error');
      setMessage('❌ No authentication token found');
      setDetails({
        info: 'Please login first to test authenticated endpoints',
      });
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        method: 'GET',
        credentials: 'include',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      setStatus('success');
      setMessage('✅ Authentication is working!');
      setDetails({
        user: data,
        token_prefix: token.substring(0, 20) + '...',
      });
    } catch (error) {
      setStatus('error');
      setMessage(`❌ Auth Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setDetails({
        error: error instanceof Error ? error.message : 'Unknown error',
        token_found: !!token,
      });
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>CORS Configuration Test</CardTitle>
        <CardDescription>
          Test your CORS and authentication setup between frontend and backend
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            <strong>Frontend:</strong> {typeof window !== 'undefined' ? window.location.origin : 'N/A'}
          </p>
          <p className="text-sm text-muted-foreground">
            <strong>Backend:</strong> {API_URL}
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={testCORS}
            disabled={status === 'loading'}
            variant="outline"
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              'Test CORS'
            )}
          </Button>

          <Button
            onClick={testAuth}
            disabled={status === 'loading'}
            variant="outline"
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Auth'
            )}
          </Button>
        </div>

        {status !== 'idle' && (
          <Alert variant={status === 'success' ? 'default' : 'destructive'}>
            <div className="flex items-start gap-2">
              {status === 'success' ? (
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              ) : status === 'error' ? (
                <XCircle className="h-5 w-5" />
              ) : (
                <Loader2 className="h-5 w-5 animate-spin" />
              )}
              <div className="flex-1">
                <AlertDescription className="font-medium">
                  {message}
                </AlertDescription>
                {details && (
                  <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto max-h-64">
                    {JSON.stringify(details, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          </Alert>
        )}

        <div className="pt-4 border-t space-y-2">
          <h4 className="font-semibold text-sm">Common Issues:</h4>
          <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
            <li>Backend server not running → Start with <code>uvicorn app.main:app --reload</code></li>
            <li>CORS policy error → Check CORS middleware configuration</li>
            <li>Wrong API URL → Verify NEXT_PUBLIC_API_URL environment variable</li>
            <li>Credentials not working → Ensure <code>credentials: 'include'</code> in fetch</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
