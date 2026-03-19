'use client'

import React, { useState } from 'react'
import { SidebarProvider } from '@/components/ui/sidebar'
import Sidebar from '@/components/sidebar'
import TopBar from '@/components/top-bar'
import ProtectedRoute from '@/components/ProtectedRoute'

// Import all page components
import DashboardPage from '@/components/pages/dashboard'
import OverviewPage from '@/components/pages/overview'
import RepositoriesPage from '@/components/pages/repositories'
import ArchitecturePage from '@/components/pages/architecture'
import RiskDebtPage from '@/components/pages/risk-debt'
import ScanHistoryPage from '@/components/pages/scan-history'
import ImpactSimulatorPage from '@/components/pages/impact-simulator'
import AIInsightsPage from '@/components/pages/ai-insights'
import SettingsPage from '@/components/pages/settings'

export default function DashboardLayout() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />
      case 'overview':
        return <OverviewPage />
      case 'repositories':
        return <RepositoriesPage />
      case 'architecture':
        return <ArchitecturePage />
      case 'risk-debt':
        return <RiskDebtPage />
      case 'scan-history':
        return <ScanHistoryPage />
      case 'impact-simulator':
        return <ImpactSimulatorPage />
      case 'ai-insights':
        return <AIInsightsPage />
      case 'settings':
        return <SettingsPage />
      default:
        return <DashboardPage />
    }
  }

  return (
    <ProtectedRoute>
      <SidebarProvider>
        <div className="flex h-screen w-full overflow-hidden bg-background">
          <Sidebar currentPage={activeTab} onNavigate={setActiveTab} />
          
          <div className="flex flex-col flex-1 overflow-hidden">
            <TopBar />
            
            <main className="flex-1 overflow-y-auto p-6">
              {renderContent()}
            </main>
          </div>
        </div>
      </SidebarProvider>
    </ProtectedRoute>
  )
}
