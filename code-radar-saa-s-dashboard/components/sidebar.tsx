'use client'

import React from 'react'
import { cn } from '@/lib/utils'
import { BarChart3, LucideBrackets as CodeBrackets, GitBranch, AlertTriangle, Zap, Sparkles, Clock, Settings, MapPin, Github, ShieldCheck } from 'lucide-react'
import { useUser } from '@/context/user-context'

interface SidebarProps {
  currentPage: string
  onNavigate: (page: any) => void
}

const navigationItems = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'repositories', label: 'Repositories', icon: Github },
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'architecture', label: 'Architecture', icon: MapPin },
  { id: 'risk-debt', label: 'Risk & Debt', icon: AlertTriangle },
  { id: 'impact-simulator', label: 'Impact Simulator', icon: Zap },
  { id: 'ai-insights', label: 'AI Insights', icon: Sparkles },
  { id: 'scan-history', label: 'Scan History', icon: Clock },
]

export default function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  const { user } = useUser()
  return (
    <aside className="w-64 bg-secondary border-r border-border flex flex-col h-screen overflow-hidden">
      {/* Logo Section */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary/80 rounded-lg flex items-center justify-center shadow-lg">
            <CodeBrackets className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground tracking-tight">CodeRadar</h1>
            <p className="text-xs text-muted-foreground">Code Analysis</p>
          </div>
        </div>
      </div>

      {/* Repository Info */}
      <div className="px-6 py-4 border-b border-border/50">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Active Repository</p>
        <p className="text-sm font-medium text-foreground mt-2 truncate">coderadar/main-app</p>
        <div className="flex items-center gap-2 mt-2 text-xs">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulseGlow"></div>
          <span className="text-muted-foreground">Last scan: 2 hours ago</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        {navigationItems.map((item) => {
          const IconComponent = item.icon
          const isActive = currentPage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-md'
                  : 'text-muted-foreground hover:text-foreground hover:bg-primary/10'
              )}
            >
              <IconComponent className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Bottom – Admin + Settings */}
      <div className="px-3 py-4 border-t border-border/50 space-y-1">
        {user?.role === 'admin' && (
          <button
            onClick={() => onNavigate('admin')}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
              currentPage === 'admin'
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'text-muted-foreground hover:text-amber-400 hover:bg-amber-500/10'
            )}
          >
            <ShieldCheck className="w-5 h-5 flex-shrink-0" />
            <span>Admin Panel</span>
          </button>
        )}
        <button
          onClick={() => onNavigate('settings')}
          className={cn(
            'w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
            currentPage === 'settings'
              ? 'bg-primary text-primary-foreground shadow-md'
              : 'text-muted-foreground hover:text-foreground hover:bg-primary/10'
          )}
        >
          <Settings className="w-5 h-5 flex-shrink-0" />
          <span>Settings</span>
        </button>
      </div>
    </aside>
  )
}
