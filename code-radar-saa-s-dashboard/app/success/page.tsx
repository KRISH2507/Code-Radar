'use client'

import React, { useEffect, useState } from 'react'
import { CheckCircle2, ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'

export default function SuccessPage() {
  const [userName, setUserName] = useState('')
  const router = useRouter()

  useEffect(() => {
    const name = localStorage.getItem('pendingName') || 'there'
    setUserName(name)

    // Check if the user actually has a valid auth token
    if (!isAuthenticated()) {
      // No token means something went wrong, redirect to login
      router.push('/login')
      return
    }

    // Auto-redirect after 3 seconds
    const timer = setTimeout(() => {
      router.push('/dashboard')
    }, 3000)

    return () => clearTimeout(timer)
  }, [router])

  const handleContinue = () => {
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen w-full bg-background flex items-center justify-center p-6">
      {/* Background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-20 right-1/4 w-80 h-80 rounded-full bg-gradient-to-br from-primary/30 to-transparent blur-3xl animate-parallax-drift"></div>
        <div className="absolute bottom-32 left-1/3 w-96 h-96 rounded-full bg-gradient-to-tr from-blue-500/20 to-transparent blur-3xl animate-parallax-drift" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 right-0 w-72 h-72 rounded-full bg-gradient-to-l from-cyan-500/20 to-transparent blur-3xl animate-parallax-drift" style={{ animationDelay: '2s' }}></div>
      </div>

      <div className="relative w-full max-w-md">
        {/* Success Animation */}
        <div className="text-center mb-8 animate-fadeInUp">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-primary/20 to-blue-600/20 rounded-full mb-6 relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary to-blue-600 rounded-full animate-pulseGlow opacity-50"></div>
            <CheckCircle2 className="w-12 h-12 text-primary relative z-10" />
          </div>

          <h2 className="text-4xl font-bold mb-3">
            Welcome aboard{userName !== 'there' ? `, ${userName.split(' ')[0]}` : ''}!
          </h2>
          <p className="text-lg text-muted-foreground mb-2">
            Your account has been created successfully
          </p>
          <div className="inline-flex items-center gap-2 text-sm text-primary">
            <Sparkles className="w-4 h-4" />
            <span>Let&apos;s start exploring your codebase</span>
          </div>
        </div>

        {/* Success Card */}
        <div className="bg-card border border-border rounded-2xl p-8 shadow-xl backdrop-blur-sm animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
          <div className="space-y-4 mb-6">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-sm">Account verified</p>
                <p className="text-xs text-muted-foreground">Your email has been confirmed</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-sm">Free trial activated</p>
                <p className="text-xs text-muted-foreground">14 days of full access</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
              <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-sm">Dashboard ready</p>
                <p className="text-xs text-muted-foreground">Start analyzing your code now</p>
              </div>
            </div>
          </div>

          <Button
            onClick={handleContinue}
            className="w-full bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-700 text-primary-foreground py-6 text-base font-medium group"
          >
            Go to Dashboard
            <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition" />
          </Button>

          <p className="text-xs text-center text-muted-foreground mt-4">
            Redirecting automatically in a moment...
          </p>
        </div>

        {/* Additional Info */}
        <div className="text-center mt-6 text-sm text-muted-foreground animate-fadeInUp" style={{ animationDelay: '0.4s' }}>
          <p>Need help? Check out our <a href="#" className="text-primary hover:underline">Quick Start Guide</a></p>
        </div>
      </div>
    </div>
  )
}
