'use client'

import React, { useState } from 'react'
import { ArrowRight, Mail, Chrome, Lock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { login, googleAuth } from '@/lib/api'
import { useRouter } from 'next/navigation'

declare global {
  interface Window {
    google?: any;
  }
}

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const { data, error: apiError } = await login(email, password)

      if (apiError) {
        setError(apiError)
        setLoading(false)
        return
      }

      // Store email for OTP verification
      localStorage.setItem('pendingEmail', email)

      // Redirect to OTP page
      router.push('/otp')
    } catch (err) {
      setError('An unexpected error occurred')
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setError('')
    setGoogleLoading(true)

    try {
      const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID

      if (!googleClientId) {
        setError('Google Client ID not configured')
        setGoogleLoading(false)
        return
      }

      // Load Google Identity Services script if not already loaded
      if (!window.google?.accounts) {
        const script = document.createElement('script')
        script.src = 'https://accounts.google.com/gsi/client'
        script.async = true
        script.defer = true

        await new Promise<void>((resolve, reject) => {
          script.onload = () => resolve()
          script.onerror = () => reject(new Error('Failed to load Google script'))
          document.head.appendChild(script)
        })

        await new Promise(resolve => setTimeout(resolve, 500))
      }

      // Initialize Google Sign-In with ID token callback
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: any) => {
          // Remove overlay if present
          document.getElementById('google-signin-overlay')?.remove()

          if (response.credential) {
            const { data, error: apiError } = await googleAuth(response.credential)

            if (apiError) {
              setError(apiError)
              setGoogleLoading(false)
              return
            }

            if (data?.access_token) {
              localStorage.setItem('access_token', data.access_token)
              localStorage.setItem('authMethod', 'google')
              router.push('/dashboard')
            } else {
              setError('Invalid response from server')
              setGoogleLoading(false)
            }
          } else {
            setError('Google sign-in was cancelled')
            setGoogleLoading(false)
          }
        },
        auto_select: false,
        cancel_on_tap_outside: false,
      })

      // Try the One Tap prompt first
      window.google.accounts.id.prompt((notification: any) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          // Fallback: render a visible Google Sign-In button in an overlay
          const overlay = document.createElement('div')
          overlay.id = 'google-signin-overlay'
          overlay.style.cssText = 'position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.6);'

          const card = document.createElement('div')
          card.style.cssText = 'background:#1a1a2e;padding:32px;border-radius:16px;text-align:center;min-width:320px;'

          const title = document.createElement('p')
          title.textContent = 'Sign in with Google'
          title.style.cssText = 'color:white;font-size:16px;margin-bottom:20px;font-weight:500;'
          card.appendChild(title)

          const btnContainer = document.createElement('div')
          btnContainer.style.cssText = 'display:flex;justify-content:center;'
          card.appendChild(btnContainer)

          window.google.accounts.id.renderButton(btnContainer, {
            theme: 'filled_blue',
            size: 'large',
            width: 280,
            text: 'signin_with',
          })

          const cancelBtn = document.createElement('button')
          cancelBtn.textContent = 'Cancel'
          cancelBtn.style.cssText = 'margin-top:16px;color:#aaa;background:none;border:1px solid #555;padding:8px 24px;border-radius:8px;cursor:pointer;font-size:14px;'
          cancelBtn.onclick = () => {
            overlay.remove()
            setGoogleLoading(false)
          }
          card.appendChild(cancelBtn)

          overlay.appendChild(card)
          overlay.onclick = (e) => {
            if (e.target === overlay) {
              overlay.remove()
              setGoogleLoading(false)
            }
          }
          document.body.appendChild(overlay)
        }
      })
    } catch (err) {
      setError('Google login failed. Please try again.')
      setGoogleLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-background flex items-center justify-center p-6">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-20 right-1/4 w-80 h-80 rounded-full bg-gradient-to-br from-primary/30 to-transparent blur-3xl animate-parallax-drift"></div>
        <div className="absolute bottom-32 left-1/3 w-96 h-96 rounded-full bg-gradient-to-tr from-blue-500/20 to-transparent blur-3xl animate-parallax-drift" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-blue-600 rounded-lg flex items-center justify-center font-bold text-xl text-primary-foreground shadow-lg">
              ◈
            </div>
            <h1 className="font-bold text-2xl tracking-tight">CodeRadar</h1>
          </div>
          <h2 className="text-3xl font-bold mb-2">Welcome back</h2>
          <p className="text-muted-foreground">Log in to your account</p>
        </div>

        {/* Login Card */}
        <div className="bg-card border border-border rounded-2xl p-8 shadow-xl backdrop-blur-sm">
          {/* Google Login */}
          <Button
            onClick={handleGoogleLogin}
            variant="outline"
            disabled={googleLoading}
            className="w-full py-6 text-base font-medium mb-6 hover:bg-secondary/50"
          >
            <Chrome className="w-5 h-5 mr-2" />
            {googleLoading ? 'Connecting...' : 'Continue with Google'}
          </Button>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-card text-muted-foreground">or</span>
            </div>
          </div>

          {/* Email Login Form */}
          <form onSubmit={handleEmailLogin} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                className="py-6 text-base"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                className="py-6 text-base"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-700 text-primary-foreground py-6 text-base font-medium group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>Processing...</>
              ) : (
                <>
                  <Lock className="w-5 h-5 mr-2" />
                  Continue with Email
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition" />
                </>
              )}
            </Button>
          </form>

          {/* Forgot Password */}
          <div className="text-center mt-4">
            <a href="#" className="text-sm text-primary hover:underline">
              Forgot password?
            </a>
          </div>
        </div>

        {/* Signup Link */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          Don&apos;t have an account?{' '}
          <a href="/signup" className="text-primary hover:underline font-medium">
            Sign up
          </a>
        </p>

        {/* Back to Home */}
        <div className="text-center mt-4">
          <a href="/" className="text-sm text-muted-foreground hover:text-foreground transition">
            ← Back to Home
          </a>
        </div>
      </div>
    </div>
  )
}
