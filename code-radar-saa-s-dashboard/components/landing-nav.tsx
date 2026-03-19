'use client'

import React, { useEffect, useState } from 'react'
import { Sun, Moon } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface LandingNavProps {
  onNavigateToDashboard?: () => void
}

export default function LandingNav({ onNavigateToDashboard }: LandingNavProps) {
  const [mounted, setMounted] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem('coderadar-theme') as 'light' | 'dark' | null
    if (stored) {
      setTheme(stored)
      document.documentElement.classList.toggle('light', stored === 'light')
    } else {
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('coderadar-theme', newTheme)
    document.documentElement.classList.toggle('light', newTheme === 'light')
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  if (!mounted) {
    return (
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 backdrop-blur-md bg-background/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-blue-600 rounded-lg flex items-center justify-center font-bold text-lg text-primary-foreground shadow-lg">
              ◈
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight">CodeRadar</h1>
              <p className="text-xs text-muted-foreground">Code Intelligence</p>
            </div>
          </div>
        </div>
      </nav>
    )
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 backdrop-blur-md bg-background/50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-blue-600 rounded-lg flex items-center justify-center font-bold text-lg text-primary-foreground shadow-lg shadow-primary/40">
            ◈
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">CodeRadar</h1>
            <p className="text-xs text-muted-foreground">Code Intelligence</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={toggleTheme}
            className="p-2.5 rounded-lg transition-all duration-200 text-muted-foreground hover:text-foreground hover:bg-secondary/50"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          <div className="flex items-center gap-3">
            <Button 
              onClick={() => window.location.href = '/login'}
              variant="ghost"
              className="font-medium"
            >
              Login
            </Button>
            <Button 
              onClick={() => window.location.href = '/signup'}
              className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-700 text-primary-foreground border-0 shadow-lg shadow-primary/40 font-medium"
            >
              Sign Up
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}
