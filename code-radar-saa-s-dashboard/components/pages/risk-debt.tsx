'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertTriangle, Lightbulb } from 'lucide-react'

const riskData = [
  { reason: 'High Complexity', count: 24 },
  { reason: 'Duplication', count: 18 },
  { reason: 'Large Files', count: 15 },
  { reason: 'Deep Nesting', count: 12 },
  { reason: 'Unused Imports', count: 8 },
]

const severityData = [
  { name: 'Critical', value: 5 },
  { name: 'High', value: 18 },
  { name: 'Medium', value: 42 },
  { name: 'Low', value: 35 },
]

const colors = ['#ef4444', '#f97316', '#eab308', '#84cc16']

export default function RiskDebtPage() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Risk & Technical Debt</h1>
        <p className="text-muted-foreground">High-risk files and refactoring recommendations</p>
      </div>

      {/* Risk Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Critical Issues', value: '5', color: 'bg-red-500/10 text-red-400' },
          { label: 'High Priority', value: '18', color: 'bg-orange-500/10 text-orange-400' },
          { label: 'Medium Priority', value: '42', color: 'bg-yellow-500/10 text-yellow-400' },
          { label: 'Total Debt Score', value: '38', color: 'bg-blue-500/10 text-blue-400' },
        ].map((item, idx) => (
          <Card key={idx} className={`p-6 border-border bg-card`}>
            <p className="text-sm text-muted-foreground mb-2">{item.label}</p>
            <h3 className={`text-3xl font-bold ${item.color}`}>{item.value}</h3>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Breakdown */}
        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-6">Risk Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="reason" stroke="hsl(var(--muted-foreground))" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
              />
              <Bar dataKey="count" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Severity Distribution */}
        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-6">Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* High-Risk Files Table */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          High-Risk Files
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">File</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Risk Level</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Complexity</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Issues</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {[
                { file: 'packages/core/index.ts', risk: 'Critical', complexity: 92, issues: 8, status: 'Needs Review' },
                { file: 'apps/web/middleware.ts', risk: 'High', complexity: 87, issues: 5, status: 'In Review' },
                { file: 'lib/utils/transform.ts', risk: 'High', complexity: 78, issues: 4, status: 'Flagged' },
                { file: 'src/api/handler.ts', risk: 'Medium', complexity: 65, issues: 3, status: 'Monitored' },
              ].map((row, idx) => (
                <tr key={idx} className="border-b border-border hover:bg-secondary/30 transition-colors">
                  <td className="py-4 px-4 text-foreground font-medium">{row.file}</td>
                  <td className="py-4 px-4">
                    <span className={`px-3 py-1 rounded text-xs font-medium ${
                      row.risk === 'Critical' ? 'bg-red-500/20 text-red-400' :
                      row.risk === 'High' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {row.risk}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-foreground">{row.complexity}</td>
                  <td className="py-4 px-4 text-foreground">{row.issues}</td>
                  <td className="py-4 px-4 text-muted-foreground text-xs">{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recommendations */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          Refactoring Recommendations
        </h3>
        <div className="space-y-4">
          {[
            { title: 'Break down large functions', description: 'packages/core/index.ts has 3 functions over 100 lines', impact: 'High' },
            { title: 'Remove code duplication', description: 'lib/utils/transform.ts shares 42% with utils/helpers.ts', impact: 'Medium' },
            { title: 'Extract common logic', description: 'apps/web/middleware.ts and api/middleware.ts share patterns', impact: 'High' },
            { title: 'Update dependencies', description: '3 dependencies have security updates available', impact: 'Critical' },
          ].map((rec, idx) => (
            <div key={idx} className="p-4 rounded-lg bg-secondary/50 border border-border/50 hover:border-border transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">{rec.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{rec.description}</p>
                </div>
                <span className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap ml-4 ${
                  rec.impact === 'Critical' ? 'bg-red-500/20 text-red-400' :
                  rec.impact === 'High' ? 'bg-orange-500/20 text-orange-400' :
                  'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {rec.impact}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
