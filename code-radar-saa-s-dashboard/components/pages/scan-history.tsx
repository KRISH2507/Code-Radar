'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Calendar, TrendingDown } from 'lucide-react'

const debtTrendData = [
  { date: 'Jan 1', debt: 72, complexity: 58, duplication: 24 },
  { date: 'Jan 8', debt: 68, complexity: 55, duplication: 22 },
  { date: 'Jan 15', debt: 65, complexity: 52, duplication: 20 },
  { date: 'Jan 22', debt: 62, complexity: 50, duplication: 18 },
  { date: 'Jan 29', debt: 58, complexity: 48, duplication: 16 },
  { date: 'Feb 5', debt: 55, complexity: 45, duplication: 15 },
  { date: 'Feb 12', debt: 52, complexity: 42, duplication: 13 },
]

const scanHistoryData = [
  { date: 'Feb 12, 2024', files: 2847, languages: 8, issues: 65, duration: '3m 42s', status: 'Completed' },
  { date: 'Feb 5, 2024', files: 2821, languages: 8, issues: 72, duration: '3m 28s', status: 'Completed' },
  { date: 'Jan 29, 2024', files: 2805, languages: 8, issues: 78, duration: '3m 35s', status: 'Completed' },
  { date: 'Jan 22, 2024', files: 2789, languages: 8, issues: 85, duration: '3m 51s', status: 'Completed' },
  { date: 'Jan 15, 2024', files: 2756, languages: 8, issues: 92, duration: '3m 22s', status: 'Completed' },
]

export default function ScanHistoryPage() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Scan History & Trends</h1>
        <p className="text-muted-foreground">Track codebase metrics over time</p>
      </div>

      {/* Trend Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: 'Debt Score', value: '55', change: '-26%', trend: 'down' },
          { label: 'Avg Complexity', value: '42', change: '-27%', trend: 'down' },
          { label: 'Code Duplication', value: '13%', change: '-46%', trend: 'down' },
        ].map((item, idx) => (
          <Card key={idx} className="p-6 border-border bg-card">
            <p className="text-sm text-muted-foreground mb-2">{item.label}</p>
            <div className="flex items-end justify-between">
              <h3 className="text-3xl font-bold text-foreground">{item.value}</h3>
              <span className="flex items-center gap-1 text-sm font-semibold text-green-400">
                <TrendingDown className="w-4 h-4" />
                {item.change}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Multi-line Chart */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6">Trend Analysis (Last 30 Days)</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={debtTrendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" />
            <Tooltip 
              contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="debt" 
              stroke="hsl(var(--primary))" 
              dot={{ fill: 'hsl(var(--primary))', r: 4 }}
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="complexity" 
              stroke="hsl(var(--chart-2))" 
              dot={{ fill: 'hsl(var(--chart-2))', r: 4 }}
              strokeWidth={2}
            />
            <Line 
              type="monotone" 
              dataKey="duplication" 
              stroke="hsl(var(--chart-3))" 
              dot={{ fill: 'hsl(var(--chart-3))', r: 4 }}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Scan History Table */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-primary" />
          Scan History
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Date</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Files Analyzed</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Languages</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Issues Found</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Duration</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {scanHistoryData.map((scan, idx) => (
                <tr key={idx} className="border-b border-border hover:bg-secondary/30 transition-colors cursor-pointer">
                  <td className="py-4 px-4 text-foreground font-medium">{scan.date}</td>
                  <td className="py-4 px-4 text-foreground">{scan.files}</td>
                  <td className="py-4 px-4 text-foreground">{scan.languages}</td>
                  <td className="py-4 px-4 text-foreground">{scan.issues}</td>
                  <td className="py-4 px-4 text-muted-foreground">{scan.duration}</td>
                  <td className="py-4 px-4">
                    <span className="px-3 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400">
                      {scan.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Key Improvements */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6">Key Improvements</h3>
        <div className="space-y-3">
          {[
            { item: 'Refactored API middleware', impact: '+15% health improvement', date: 'Feb 1' },
            { item: 'Consolidated duplicate utilities', impact: '-8% code duplication', date: 'Jan 28' },
            { item: 'Extracted large components', impact: '-22% complexity', date: 'Jan 15' },
            { item: 'Updated dependencies', impact: 'Security & performance', date: 'Jan 8' },
          ].map((imp, idx) => (
            <div key={idx} className="flex items-start justify-between p-4 rounded-lg bg-secondary/50 border border-border/50">
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{imp.item}</p>
                <p className="text-xs text-muted-foreground mt-1">{imp.date}</p>
              </div>
              <span className="px-3 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400 whitespace-nowrap ml-4">
                {imp.impact}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
