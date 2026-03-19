'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Zap, TrendingUp } from 'lucide-react'

const impactData = [
  { module: 'API', affected: 15 },
  { module: 'Store', affected: 8 },
  { module: 'Utils', affected: 24 },
  { module: 'Hooks', affected: 12 },
  { module: 'Components', affected: 32 },
]

const severityData = [
  { time: '0:00', severity: 95 },
  { time: '1:00', severity: 92 },
  { time: '2:00', severity: 78 },
  { time: '3:00', severity: 65 },
  { time: '4:00', severity: 52 },
  { time: '5:00', severity: 38 },
]

export default function ImpactSimulatorPage() {
  const [selectedFile, setSelectedFile] = useState('packages/core/index.ts')
  const [simulated, setSimulated] = useState(false)

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Impact Simulator</h1>
        <p className="text-muted-foreground">Simulate code changes and view the impact on your codebase</p>
      </div>

      {/* Simulator Controls */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6">Simulate Code Change</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Select File</label>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option>packages/core/index.ts</option>
              <option>apps/web/middleware.ts</option>
              <option>lib/utils/transform.ts</option>
              <option>src/api/handler.ts</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Change Type</label>
            <div className="grid grid-cols-2 gap-3">
              {['Refactor', 'Remove', 'Update API', 'Optimize'].map((type) => (
                <button
                  key={type}
                  className="px-4 py-2 rounded-lg bg-secondary border border-border text-foreground hover:border-primary transition-colors text-sm"
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          <Button
            onClick={() => setSimulated(true)}
            className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <Zap className="w-4 h-4" />
            Simulate Impact
          </Button>
        </div>
      </Card>

      {simulated && (
        <>
          {/* Impact Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { label: 'Affected Files', value: '47', color: 'bg-blue-500/10 text-blue-400' },
              { label: 'Risk Level', value: 'Medium', color: 'bg-yellow-500/10 text-yellow-400' },
              { label: 'Breaking Changes', value: '3', color: 'bg-red-500/10 text-red-400' },
            ].map((item, idx) => (
              <Card key={idx} className="p-6 border-border bg-card">
                <p className="text-sm text-muted-foreground mb-2">{item.label}</p>
                <h3 className={`text-3xl font-bold ${item.color}`}>{item.value}</h3>
              </Card>
            ))}
          </div>

          {/* Impact Graph */}
          <Card className="p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Impact Severity Over Time
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={severityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="severity" 
                  stroke="hsl(var(--primary))" 
                  dot={{ fill: 'hsl(var(--primary))', r: 4 }}
                  activeDot={{ r: 6 }}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-xs text-muted-foreground text-center mt-4">Impact gradually decreases with proper refactoring strategy</p>
          </Card>

          {/* Affected Modules */}
          <Card className="p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-6">Affected Files & Modules</h3>
            <div className="space-y-3">
              {[
                { name: 'API Gateway', count: 15, severity: 'High' },
                { name: 'Store Modules', count: 8, severity: 'Medium' },
                { name: 'Utility Functions', count: 24, severity: 'High' },
                { name: 'Custom Hooks', count: 12, severity: 'Low' },
                { name: 'Component Library', count: 32, severity: 'Medium' },
              ].map((module, idx) => (
                <div key={idx} className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 border border-border/50">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">{module.name}</p>
                    <p className="text-xs text-muted-foreground">{module.count} files affected</p>
                  </div>
                  <span className={`px-3 py-1 rounded text-xs font-medium ${
                    module.severity === 'High' ? 'bg-red-500/20 text-red-400' :
                    module.severity === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {module.severity}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Recommendations */}
          <Card className="p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4">Recommendations</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-3">
                <span className="text-primary">•</span>
                <span>Update 3 breaking API signatures in API Gateway and Store modules</span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary">•</span>
                <span>Add deprecation warnings to old function signatures</span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary">•</span>
                <span>Create migration guide for component updates</span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary">•</span>
                <span>Plan a staged rollout across dependent modules</span>
              </li>
            </ul>
          </Card>
        </>
      )}
    </div>
  )
}
