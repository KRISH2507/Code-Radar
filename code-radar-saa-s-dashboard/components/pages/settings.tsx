'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Key, Database, Shield, Bell } from 'lucide-react'

export default function SettingsPage() {
  const [ignoreFolders, setIgnoreFolders] = useState('node_modules, .git, dist, build')
  const [scanFrequency, setScanFrequency] = useState('weekly')

  return (
    <div className="p-8 space-y-8 max-w-2xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
        <p className="text-muted-foreground">Configure CodeRadar for your repository</p>
      </div>

      {/* Repository Settings */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Database className="w-5 h-5 text-primary" />
          Repository Settings
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Repository Name</label>
            <input
              type="text"
              defaultValue="coderadar/main-app"
              className="w-full px-4 py-2 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              readOnly
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Primary Language</label>
            <select className="w-full px-4 py-2 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary">
              <option>TypeScript</option>
              <option>JavaScript</option>
              <option>Python</option>
              <option>Go</option>
              <option>Rust</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Repository Visibility</label>
            <div className="flex gap-3">
              <label className="flex items-center gap-2">
                <input type="radio" name="visibility" defaultChecked />
                <span className="text-sm">Public</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="visibility" />
                <span className="text-sm">Private</span>
              </label>
            </div>
          </div>
        </div>
      </Card>

      {/* Scan Configuration */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Settings className="w-5 h-5 text-primary" />
          Scan Configuration
        </h3>
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Scan Frequency</label>
            <select
              value={scanFrequency}
              onChange={(e) => setScanFrequency(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="manual">Manual Only</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Ignore Folders</label>
            <textarea
              value={ignoreFolders}
              onChange={(e) => setIgnoreFolders(e.target.value)}
              className="w-full px-4 py-2 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm h-24"
              placeholder="Comma-separated list of folders to ignore"
            />
            <p className="text-xs text-muted-foreground mt-2">Separate multiple folders with commas</p>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium text-foreground">Analysis Options</p>
            {[
              { label: 'Analyze Complexity', desc: 'Measure cyclomatic and cognitive complexity' },
              { label: 'Detect Duplication', desc: 'Find duplicated code patterns' },
              { label: 'Check Dependencies', desc: 'Map dependency graph and cycles' },
              { label: 'Security Scan', desc: 'Check for known vulnerabilities' },
            ].map((opt, idx) => (
              <label key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 border border-border/50 cursor-pointer hover:border-border transition-colors">
                <input type="checkbox" defaultChecked className="w-4 h-4" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">{opt.label}</p>
                  <p className="text-xs text-muted-foreground">{opt.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      </Card>

      {/* API Keys & Access */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Key className="w-5 h-5 text-primary" />
          API Keys & Access
        </h3>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-foreground">API Key</label>
              <Button className="text-xs bg-secondary hover:bg-secondary/80 text-foreground border border-border">
                Regenerate
              </Button>
            </div>
            <div className="p-3 rounded-lg bg-secondary border border-border flex items-center justify-between">
              <code className="text-xs text-muted-foreground font-mono truncate">cr_5x9k2j8f9q3w1e7r4t6y8u0i9o2p</code>
              <button className="text-muted-foreground hover:text-foreground transition-colors">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8 3a1 1 0 011-1h2a1 1 0 011 1v2h4a1 1 0 110 2H4a1 1 0 110-2h4V3z" />
                  <path d="M6 6a1 1 0 00-1 1v10a1 1 0 001 1h8a1 1 0 001-1V7a1 1 0 00-1-1H6z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Notifications */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Bell className="w-5 h-5 text-primary" />
          Notifications
        </h3>
        <div className="space-y-3">
          {[
            { label: 'New Issues Detected', desc: 'Notify when new high-risk code is detected' },
            { label: 'Scan Completed', desc: 'Get notified when scans finish' },
            { label: 'Health Alert', desc: 'Alert when code health drops below threshold' },
          ].map((notif, idx) => (
            <label key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 border border-border/50 cursor-pointer hover:border-border transition-colors">
              <input type="checkbox" defaultChecked className="w-4 h-4" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{notif.label}</p>
                <p className="text-xs text-muted-foreground">{notif.desc}</p>
              </div>
            </label>
          ))}
        </div>
      </Card>

      {/* Security */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary" />
          Security & Privacy
        </h3>
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-secondary/50 border border-border/50">
            <p className="text-sm font-medium text-foreground mb-2">Data Retention</p>
            <select className="w-full px-4 py-2 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm">
              <option>30 days</option>
              <option>90 days</option>
              <option>1 year</option>
              <option>Forever</option>
            </select>
          </div>
          <label className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 border border-border/50 cursor-pointer hover:border-border transition-colors">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground">Encrypt scan data</p>
              <p className="text-xs text-muted-foreground">All scan results are encrypted at rest</p>
            </div>
          </label>
        </div>
      </Card>

      {/* Save Button */}
      <div className="flex gap-3">
        <Button className="bg-primary hover:bg-primary/90 text-primary-foreground">Save Changes</Button>
        <Button className="bg-secondary hover:bg-secondary/80 text-foreground border border-border">Cancel</Button>
      </div>
    </div>
  )
}
