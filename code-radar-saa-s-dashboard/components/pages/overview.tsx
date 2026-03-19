'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { TrendingUp, AlertCircle, CheckCircle, FileText, RefreshCw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { cn } from '@/lib/utils'
import {
  getDashboardStats,
  getDashboardOverview,
  getRepositoryTrend,
  DashboardStats,
  OverviewRepo,
} from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TrendPoint {
  date: string
  score: number
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Central numeric safety guard.
 * Converts any value to a finite number; returns `fallback` (default 0)
 * if the result would be NaN, ±Infinity, null, or undefined.
 * Use this for EVERY value that comes from the API before passing it to
 * Math.round(), toFixed(), arithmetic, or JSX rendering.
 */
function safeNumber(value: unknown, fallback = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function riskLabel(healthScore: number): 'High' | 'Medium' | 'Low' {
  const score = safeNumber(healthScore)
  if (score < 40) return 'High'
  if (score < 70) return 'Medium'
  return 'Low'
}

function formatNumber(n: unknown): string {
  const num = safeNumber(n)
  if (num === 0) return '0'
  return num >= 1000 ? `${(num / 1000).toFixed(1)}k` : String(Math.round(num))
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function OverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [repos, setRepos] = useState<OverviewRepo[]>([])
  const [trendData, setTrendData] = useState<TrendPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── Fetch all dashboard data ─────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const [statsRes, overviewRes] = await Promise.all([
        getDashboardStats(),
        getDashboardOverview(),
      ])

      if (statsRes.error) {
        setError(statsRes.error)
      } else if (statsRes.data) {
        setStats(statsRes.data)
      }

      let repoList: OverviewRepo[] = []
      if (overviewRes.data) {
        repoList = overviewRes.data.recent_repositories
        setRepos(repoList)
      }

      // Trend: fetch for first completed repo
      const completedRepo = repoList.find(r => r.status === 'completed')
      if (completedRepo) {
        const trendRes = await getRepositoryTrend(completedRepo.id, 8)
        if (trendRes.data?.trend && trendRes.data.trend.length > 0) {
          setTrendData(
            trendRes.data.trend.map(t => ({
              date: new Date(t.created_at).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric',
              }),
              score: safeNumber(t.health_score),
            }))
          )
        }
      }

      setLastUpdated(new Date())
      setLoading(false)

      // ── Start / stop polling based on scanning_repos count ────────────────
      const isScanning = (statsRes.data?.scanning_repos ?? 0) > 0

      if (isScanning && !pollingRef.current) {
        // Poll stats every 5 s while a scan is running
        pollingRef.current = setInterval(async () => {
          const freshStats = await getDashboardStats()
          if (freshStats.data) {
            setStats(freshStats.data)
            setLastUpdated(new Date())

            if (freshStats.data.scanning_repos === 0) {
              // All scans finished — stop interval and do one full refresh
              clearInterval(pollingRef.current!)
              pollingRef.current = null
              fetchData()
            }
          }
        }, 5000)
      } else if (!isScanning && pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    } catch (err) {
      setError('Failed to load dashboard data')
      setLoading(false)
    }
  }, [])

  // Mount: fetch once, cleanup interval on unmount
  useEffect(() => {
    fetchData()
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [fetchData])

  // ── Derived values ────────────────────────────────────────────────────────
  // safeNumber ensures Math operations never produce NaN even if the API
  // returns null, undefined, or a non-numeric value for avg_health_score.
  const healthScore = Math.round(safeNumber(stats?.avg_health_score))
  const isScanning  = safeNumber(stats?.scanning_repos) > 0
  const hasScans    = safeNumber(stats?.completed_scans) > 0

  // Gauge arc length — explicitly safe; NaN here creates a React warning.
  const gaugeLength = (healthScore / 100) * 235

  const healthMetrics = [
    {
      label: 'Total Files Analyzed',
      value: formatNumber(stats?.total_files),
      icon: FileText,
      change: stats ? `${formatNumber(stats.total_lines)} lines` : '—',
      positive: true,
    },
    {
      label: 'Repositories',
      value: String(safeNumber(stats?.total_repositories)),
      icon: TrendingUp,
      change: `${safeNumber(stats?.completed_scans)} scanned`,
      positive: true,
    },
    {
      label: 'Overall Health Score',
      value: hasScans ? `${healthScore}%` : '—',
      icon: CheckCircle,
      change: !hasScans ? 'No scan yet' : healthScore >= 70 ? 'Good' : healthScore >= 40 ? 'Needs work' : 'Critical',
      positive: healthScore >= 70,
    },
    {
      label: 'Critical Issues',
      value: String(safeNumber(stats?.total_critical)),
      icon: AlertCircle,
      change: `${safeNumber(stats?.total_high)} high, ${safeNumber(stats?.total_medium)} medium`,
      positive: safeNumber(stats?.total_critical) === 0,
    },
  ]

  // Repos sorted by risk score (critical × 10 + high × 5 + medium)
  const riskyRepos = [...repos]
    .filter(r => r.status === 'completed')
    .sort(
      (a, b) => {
        const scoreA = safeNumber(a.critical_count) * 10 + safeNumber(a.high_count) * 5 + safeNumber(a.medium_count)
        const scoreB = safeNumber(b.critical_count) * 10 + safeNumber(b.high_count) * 5 + safeNumber(b.medium_count)
        return scoreB - scoreA
      }
    )
    .slice(0, 5)

  // ── Render ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-96">
        <div className="text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-primary animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading overview...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Codebase Overview</h1>
          <p className="text-muted-foreground mt-2">
            {isScanning ? (
              <span className="flex items-center gap-2">
                <RefreshCw className="w-3 h-3 animate-spin" />
                Scan in progress — updating every 5 s
              </span>
            ) : lastUpdated ? (
              `Last updated ${lastUpdated.toLocaleTimeString()}`
            ) : (
              'No scans yet'
            )}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-muted-foreground">Overall Health</p>
          <div className="text-5xl font-bold text-primary mt-1">
            {hasScans ? `${healthScore}%` : '—'}
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Health Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {healthMetrics.map((metric, idx) => {
          const Icon = metric.icon
          return (
            <div
              key={idx}
              className="bg-card border border-border rounded-lg p-6 hover:border-primary/30 transition-colors duration-300"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
                    {metric.label}
                  </p>
                  <p className="text-2xl font-bold text-foreground mt-2">{metric.value}</p>
                  <p className={cn('text-xs mt-2 font-medium', metric.positive ? 'text-green-400' : 'text-red-400')}>
                    {metric.change}
                  </p>
                </div>
                <Icon className="w-8 h-8 text-primary/60" />
              </div>
            </div>
          )
        })}
      </div>

      {/* Health Score Gauge + Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Gauge */}
        <div className="lg:col-span-1 bg-card border border-border rounded-lg p-8">
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-8">
            Codebase Health Score
          </h3>
          <div className="flex items-center justify-center">
            <div className="relative w-40 h-40">
              <svg viewBox="0 0 180 180" className="w-full h-full">
                {/* Background arc */}
                <path
                  d="M 30 150 A 75 75 0 0 1 150 150"
                  fill="none"
                  stroke="hsl(var(--border))"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                {/* Progress arc — driven by real health score */}
                <path
                  d="M 30 150 A 75 75 0 0 1 150 150"
                  fill="none"
                  stroke="hsl(189 100% 54%)"
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={`${gaugeLength} 235`}
                  className="transition-all duration-700"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-3xl font-bold text-foreground">
                    {hasScans ? healthScore : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {!hasScans ? 'No data' : healthScore >= 70 ? 'Good' : healthScore >= 40 ? 'Fair' : 'Poor'}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-8 space-y-2 text-sm">
            <div className="flex justify-between text-muted-foreground">
              <span>0</span><span>50</span><span>100</span>
            </div>
            <div className="h-1 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full" />
          </div>
        </div>

        {/* Health Trend */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-6">
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider mb-6">
            Health Score Trend
          </h3>
          {hasScans && trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(189 100% 54%)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(189 100% 54%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" />
                <YAxis domain={[0, 100]} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="hsl(189 100% 54%)"
                  fill="url(#colorScore)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-muted-foreground text-sm">
              {hasScans
                ? 'Trend data will appear after more scans are completed.'
                : 'No scan history yet. Add a repository and run a scan.'}
            </div>
          )}
        </div>
      </div>

      {/* Top Risky Repositories */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
            Top Risky Repositories
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            Repositories ranked by critical and high-severity issue count
          </p>
        </div>

        {riskyRepos.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            {repos.length === 0
              ? 'No repositories yet. Add one from the Repositories page.'
              : 'No completed scans yet. Waiting for scans to finish…'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-secondary/50">
                <tr className="border-b border-border">
                  <th className="px-6 py-3 text-left font-semibold text-muted-foreground">Repository</th>
                  <th className="px-6 py-3 text-left font-semibold text-muted-foreground">Risk Level</th>
                  <th className="px-6 py-3 text-left font-semibold text-muted-foreground">Top Issues</th>
                  <th className="px-6 py-3 text-right font-semibold text-muted-foreground">Files</th>
                  <th className="px-6 py-3 text-right font-semibold text-muted-foreground">Total Issues</th>
                </tr>
              </thead>
              <tbody>
                {riskyRepos.map((repo) => {
                  const risk        = riskLabel(safeNumber(repo.health_score))
                  const critCount   = safeNumber(repo.critical_count)
                  const highCount   = safeNumber(repo.high_count)
                  const medCount    = safeNumber(repo.medium_count)
                  const lowCount    = safeNumber(repo.low_count)
                  const topIssue =
                    critCount > 0
                      ? `${critCount} critical issue${critCount > 1 ? 's' : ''}`
                      : highCount > 0
                      ? `${highCount} high-severity issue${highCount > 1 ? 's' : ''}`
                      : `${medCount} medium-severity issue${medCount > 1 ? 's' : ''}`
                  const totalIssues = critCount + highCount + medCount + lowCount

                  return (
                    <tr
                      key={repo.id}
                      className="border-b border-border hover:bg-secondary/30 transition-colors"
                    >
                      <td className="px-6 py-4 font-mono text-xs text-primary">{repo.name}</td>
                      <td className="px-6 py-4">
                        <span
                          className={cn(
                            'px-2 py-1 text-xs font-medium rounded-md',
                            risk === 'High'
                              ? 'bg-red-500/20 text-red-300'
                              : risk === 'Medium'
                              ? 'bg-yellow-500/20 text-yellow-300'
                              : 'bg-green-500/20 text-green-300'
                          )}
                        >
                          {risk}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">{topIssue}</td>
                      <td className="px-6 py-4 text-right text-muted-foreground">
                        {formatNumber(safeNumber(repo.file_count))}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className="px-2 py-1 bg-primary/20 text-primary rounded-md font-medium text-xs">
                          {totalIssues}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

