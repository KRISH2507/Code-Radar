'use client'

import { useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/api'

interface ProtectedRouteProps {
  children: ReactNode
}

/**
 * Protected Route wrapper component
 * Redirects to login if user is not authenticated.
 * Uses mounted state to prevent SSR/client hydration mismatch.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [authorized, setAuthorized] = useState(false)

  useEffect(() => {
    setMounted(true)
    if (!isAuthenticated()) {
      router.push('/login')
    } else {
      setAuthorized(true)
    }
  }, [router])

  // During SSR and initial mount, render nothing to avoid hydration mismatch
  if (!mounted || !authorized) {
    return null
  }

  return <>{children}</>
}
