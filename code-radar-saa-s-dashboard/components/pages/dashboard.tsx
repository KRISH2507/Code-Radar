'use client'

import React from 'react'
import { Card } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const complexityData = [
  { file: 'index.ts', complexity: 45 },
  { file: 'utils.ts', complexity: 38 },
  { file: 'hooks.ts', complexity: 52 },
  { file: 'store.ts', complexity: 28 },
  { file: 'api.ts', complexity: 61 },
]

const dependencyData = [
  { name: 'External Deps', value: 234 },
  { name: 'Internal Deps', value: 412 },
  { name: 'Unused Deps', value: 18 },
]

const debtTrendData = [
  { month: 'Jan', debt: 65 },
  { month: 'Feb', debt: 72 },
  { month: 'Mar', debt: 58 },
  { month: 'Apr', debt: 45 },
  { month: 'May', debt: 38 },
]

const colors = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))']

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
        <p className="text-muted-foreground">Technical debt heatmap and code metrics</p>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Complexity Distribution */}
        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-6">Complexity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complexityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="file" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
                cursor={{ fill: 'rgba(255,255,255,0.1)' }}
              />
              <Bar dataKey="complexity" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Dependency Count */}
        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-6">Dependency Count</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={dependencyData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {dependencyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Technical Debt Trend */}
        <Card className="lg:col-span-2 p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-6">Technical Debt Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={debtTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" />
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
                activeDot={{ r: 6 }}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: 'Average Complexity', value: '45.2', trend: 'down' },
          { label: 'Code Duplication', value: '12.3%', trend: 'up' },
          { label: 'Maintainability Index', value: '82', trend: 'up' },
        ].map((metric, idx) => (
          <Card key={idx} className="p-6 border-border bg-card">
            <p className="text-sm text-muted-foreground mb-3">{metric.label}</p>
            <div className="flex items-end justify-between">
              <h3 className="text-2xl font-bold text-foreground">{metric.value}</h3>
              <span className={`text-xs font-medium px-2 py-1 rounded ${
                metric.trend === 'down' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {metric.trend === 'down' ? '↓ Improving' : '↑ Declining'}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
