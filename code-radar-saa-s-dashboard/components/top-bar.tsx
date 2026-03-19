'use client'

import React, { useState, useEffect } from 'react'
import { ChevronDown, Play, User, Bell, Sun, Moon, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { logout, runScan } from '@/lib/api'
import { useRepository } from '@/context/repository-context'
import PlanBadge from '@/components/PlanBadge'
import ScanQuota from '@/components/ScanQuota'

export default function TopBar() {
  const [mounted, setMounted] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const [isScanning, setIsScanning] = useState(false)
  const { activeRepo, setActiveRepo } = useRepository()

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem('coderadar-theme') as 'light' | 'dark' | null
    if (stored) {
      setTheme(stored)
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('coderadar-theme', newTheme)
    document.documentElement.classList.toggle('light', newTheme === 'light')
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  const handleRunScan = async () => {
    console.log('[TOP BAR] Run Scan button clicked')
    console.log('[TOP BAR] Active repository:', activeRepo)

    if (!activeRepo) {
      console.log('[TOP BAR] No active repository selected')
      alert('Please select a repository first')
      return
    }

    if (activeRepo.status === 'processing') {
      console.log('[TOP BAR] Repository is already being scanned')
      alert('This repository is already being scanned')
      return
    }

    console.log(`[TOP BAR] Triggering scan for repository ID: ${activeRepo.id}`)
    setIsScanning(true)

    try {
      const result = await runScan(activeRepo.id)
      console.log('[TOP BAR] Scan triggered successfully:', result)

      if (result.error) {
        console.error('[TOP BAR] Scan trigger failed:', result.error)
        alert(`Failed to trigger scan: ${result.error}`)
      } else {
        console.log('[TOP BAR] Scan started, updating repository status')
        // Update the active repository status
        setActiveRepo({
          ...activeRepo,
          status: 'processing'
        })
        alert('Scan started successfully!')
      }
    } catch (error) {
      console.error('[TOP BAR] Unexpected error:', error)
      alert('An unexpected error occurred')
    } finally {
      setIsScanning(false)
      console.log('[TOP BAR] Scan request completed')
    }
  }

  const isButtonDisabled = !activeRepo || activeRepo.status === 'processing' || isScanning

  if (!mounted) {
    return (
      <header className="h-16 bg-secondary/50 backdrop-blur-sm border-b border-border flex items-center justify-between px-8 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-card/60 border border-border/50">
            <span className="text-sm font-medium text-foreground">
              {activeRepo ? activeRepo.name : 'No repository selected'}
            </span>
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-md"
            disabled
          >
            <Play className="w-4 h-4" />
            Run New Scan
          </Button>
        </div>
      </header>
    )
  }

  return (
    <header className="h-16 bg-secondary/50 backdrop-blur-sm border-b border-border flex items-center justify-between px-8 shadow-sm">
      {/* Left Section - Repository Selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-card/60 hover:bg-card/80 transition-all duration-200 cursor-pointer border border-border/50 hover:border-border">
          <span className="text-sm font-medium text-foreground">
            {activeRepo ? activeRepo.name : 'No repository selected'}
          </span>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </div>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-3">
        <ScanQuota />

        <Button
          onClick={handleRunScan}
          disabled={isButtonDisabled}
          className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play className="w-4 h-4" />
          {isScanning ? 'Scanning...' : 'Run New Scan'}
        </Button>

        <button
          onClick={toggleTheme}
          className="relative p-2.5 rounded-lg transition-all duration-200 text-muted-foreground hover:text-foreground hover:bg-primary/10"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <button className="relative p-2.5 rounded-lg transition-all duration-200 text-muted-foreground hover:text-foreground hover:bg-primary/10">
          <Bell className="w-5 h-5" />
          <div className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulseGlow shadow-lg"></div>
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center justify-center gap-2 px-3 h-10 rounded-lg bg-primary/10 hover:bg-primary/20 transition-all duration-200 border border-primary/20 hover:border-primary/40 text-muted-foreground hover:text-primary">
              <User className="w-4 h-4" />
              <PlanBadge />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem onClick={logout} className="cursor-pointer text-red-600 focus:text-red-600">
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

