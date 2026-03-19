'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import LandingPage from '@/components/pages/landing'

export default function Page() {
  const router = useRouter()

  const handleNavigateToDashboard = () => {
    router.push('/dashboard')
  }

  return <LandingPage onNavigateToDashboard={handleNavigateToDashboard} />
}
