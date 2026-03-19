'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

interface Repository {
  id: number
  name: string
  source_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  repo_url?: string
}

interface RepositoryContextType {
  activeRepo: Repository | null
  setActiveRepo: (repo: Repository | null) => void
}

const RepositoryContext = createContext<RepositoryContextType | undefined>(undefined)

export function RepositoryProvider({ children }: { children: ReactNode }) {
  const [activeRepo, setActiveRepo] = useState<Repository | null>(null)

  return (
    <RepositoryContext.Provider value={{ activeRepo, setActiveRepo }}>
      {children}
    </RepositoryContext.Provider>
  )
}

export function useRepository() {
  const context = useContext(RepositoryContext)
  if (context === undefined) {
    throw new Error('useRepository must be used within a RepositoryProvider')
  }
  return context
}
