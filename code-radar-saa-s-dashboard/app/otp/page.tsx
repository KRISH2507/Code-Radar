'use client'

import React, { useState, useRef, useEffect } from 'react'
import { ArrowRight, Mail, ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { verifyOTP, resendOTP } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function OTPPage() {
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState('')
  const [resendMsg, setResendMsg] = useState('')
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  const router = useRouter()

  useEffect(() => {
    // Get email from localStorage
    const pendingEmail = localStorage.getItem('pendingEmail')

    if (!pendingEmail) {
      // Redirect to login if no email found
      router.push('/login')
      return
    }

    setEmail(pendingEmail)

    // Focus first input
    inputRefs.current[0]?.focus()
  }, [router])

  const handleChange = (index: number, value: string) => {
    if (value.length > 1) {
      value = value[0]
    }

    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').slice(0, 6)
    const newOtp = [...otp]

    for (let i = 0; i < pastedData.length; i++) {
      if (/^\d$/.test(pastedData[i])) {
        newOtp[i] = pastedData[i]
      }
    }

    setOtp(newOtp)
    inputRefs.current[Math.min(pastedData.length, 5)]?.focus()
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    const otpValue = otp.join('')

    if (otpValue.length !== 6) {
      setError('Please enter a complete 6-digit code')
      return
    }

    setError('')
    setLoading(true)

    try {
      const { data, error: apiError } = await verifyOTP(email, otpValue)

      if (apiError) {
        setError(apiError)
        setLoading(false)
        return
      }

      // Store the access token
      if (data?.access_token) {
        localStorage.setItem('access_token', data.access_token)
        localStorage.removeItem('pendingEmail')

        // Redirect to dashboard
        router.push('/dashboard')
      } else {
        setError('Invalid response from server')
        setLoading(false)
      }
    } catch (err) {
      setError('An unexpected error occurred')
      setLoading(false)
    }
  }

  const handleResend = async () => {
    setOtp(['', '', '', '', '', ''])
    setError('')
    setResendMsg('')
    setResending(true)
    inputRefs.current[0]?.focus()

    try {
      const { error: apiError } = await resendOTP(email)

      if (apiError) {
        setError(apiError)
      } else {
        setResendMsg('A new verification code has been sent to your email.')
      }
    } catch (err) {
      setError('Failed to resend code')
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-muted p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="backdrop-blur-xl bg-card/50 border border-border/50 rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <Mail className="w-8 h-8 text-primary" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent mb-2">
              Check your email
            </h1>
            <p className="text-muted-foreground">
              We&apos;ve sent a 6-digit verification code to
            </p>
            <p className="text-foreground font-medium mt-1">{email}</p>
          </div>

          {/* Form */}
          <form onSubmit={handleVerify} className="space-y-6">
            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Success Message */}
            {resendMsg && (
              <Alert>
                <Mail className="h-4 w-4" />
                <AlertDescription>{resendMsg}</AlertDescription>
              </Alert>
            )}

            {/* OTP Input */}
            <div>
              <label className="block text-sm font-medium mb-3 text-center">
                Enter verification code
              </label>
              <div className="flex gap-2 justify-center" onPaste={handlePaste}>
                {otp.map((digit, index) => (
                  <Input
                    key={index}
                    ref={(el) => {
                      inputRefs.current[index] = el
                    }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    disabled={loading}
                    className="w-12 h-14 text-center text-2xl font-bold"
                    pattern="\d*"
                  />
                ))}
              </div>
            </div>

            <Button
              type="submit"
              disabled={otp.join('').length !== 6 || loading}
              className="w-full bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-700 text-primary-foreground py-6 text-base font-medium group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>Verifying...</>
              ) : (
                <>
                  Verify & Continue
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition" />
                </>
              )}
            </Button>
          </form>

          {/* Resend */}
          <div className="text-center mt-6">
            <p className="text-sm text-muted-foreground mb-2">
              Didn&apos;t receive the code?
            </p>
            <button
              onClick={handleResend}
              disabled={resending}
              className="text-sm text-primary hover:underline font-medium inline-flex items-center gap-1"
            >
              <RefreshCw className={`w-3 h-3 ${resending ? 'animate-spin' : ''}`} />
              {resending ? 'Resending...' : 'Resend code'}
            </button>
          </div>
        </div>

        {/* Back Link */}
        <div className="text-center mt-6">
          <a
            href="/login"
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to login
          </a>
        </div>
      </div>
    </div>
  )
}
