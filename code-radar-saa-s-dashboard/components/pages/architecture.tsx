'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Search, ZoomIn, ZoomOut, Eye } from 'lucide-react'

export default function ArchitecturePage() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [zoom, setZoom] = useState(100)

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Architecture Explorer</h1>
        <p className="text-muted-foreground">Interactive dependency graph visualization</p>
      </div>

      {/* Controls */}
      <div className="flex gap-4 flex-wrap">
        <div className="flex-1 min-w-64 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search modules..."
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-card border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setZoom(Math.max(50, zoom - 10))}
            className="p-2 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground transition-colors"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="px-4 py-2 rounded-lg bg-card border border-border text-foreground">{zoom}%</span>
          <button
            onClick={() => setZoom(Math.min(200, zoom + 10))}
            className="p-2 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground transition-colors"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <Card className="p-6 border-border bg-card h-96 relative">
        {/* Simplified Graph Visualization */}
        <svg className="w-full h-full" style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}>
          {/* Lines connecting nodes */}
          <line x1="100" y1="80" x2="300" y2="80" stroke="hsl(var(--border))" strokeWidth="2" />
          <line x1="300" y1="80" x2="500" y2="80" stroke="hsl(var(--border))" strokeWidth="2" />
          <line x1="300" y1="80" x2="300" y2="200" stroke="hsl(var(--border))" strokeWidth="2" />
          <line x1="100" y1="80" x2="100" y2="200" stroke="hsl(var(--border))" strokeWidth="2" />

          {/* Nodes */}
          {[
            { x: 100, y: 80, label: 'Core', id: 'core' },
            { x: 300, y: 80, label: 'Utils', id: 'utils' },
            { x: 500, y: 80, label: 'API', id: 'api' },
            { x: 100, y: 200, label: 'Hooks', id: 'hooks' },
            { x: 300, y: 200, label: 'Store', id: 'store' },
          ].map((node) => (
            <g
              key={node.id}
              onClick={() => setSelectedNode(node.id)}
              className="cursor-pointer"
            >
              <circle
                cx={node.x}
                cy={node.y}
                r="30"
                fill={selectedNode === node.id ? 'hsl(var(--primary))' : 'hsl(var(--card))'}
                stroke={selectedNode === node.id ? 'hsl(var(--primary))' : 'hsl(var(--border))'}
                strokeWidth="2"
              />
              <text
                x={node.x}
                y={node.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill={selectedNode === node.id ? 'hsl(var(--primary-foreground))' : 'hsl(var(--foreground))'}
                className="text-xs font-semibold"
              >
                {node.label}
              </text>
            </g>
          ))}
        </svg>
      </Card>

      {/* File Details Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left - Module List */}
        <Card className="p-6 border-border bg-card">
          <h3 className="text-lg font-semibold text-foreground mb-4">Modules</h3>
          <div className="space-y-2">
            {['Core', 'Utils', 'API', 'Hooks', 'Store', 'Components'].map((mod) => (
              <button
                key={mod}
                onClick={() => setSelectedNode(mod.toLowerCase())}
                className="w-full text-left px-4 py-2 rounded-lg bg-secondary/50 border border-border/50 text-foreground hover:border-border transition-colors text-sm"
              >
                {mod}
              </button>
            ))}
          </div>
        </Card>

        {/* Right - Details */}
        {selectedNode && (
          <Card className="lg:col-span-2 p-6 border-border bg-card">
            <h3 className="text-lg font-semibold text-foreground mb-4 capitalize flex items-center gap-2">
              <Eye className="w-4 h-4 text-primary" />
              {selectedNode} Module
            </h3>
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">Files</p>
                <p className="text-sm text-foreground">24 files</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">Outgoing Dependencies</p>
                <div className="flex gap-2 flex-wrap">
                  {['utils', 'store', 'api'].map((dep) => (
                    <span key={dep} className="px-3 py-1 rounded bg-secondary border border-border text-xs text-foreground">
                      {dep}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">Incoming Dependencies</p>
                <div className="flex gap-2 flex-wrap">
                  {['components', 'hooks'].map((dep) => (
                    <span key={dep} className="px-3 py-1 rounded bg-secondary border border-border text-xs text-foreground">
                      {dep}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
