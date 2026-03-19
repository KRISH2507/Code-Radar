'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, Plus, GitBranch, Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { submitGitHubRepo, uploadZipFile, getUserRepositories, deleteRepository, isAuthenticated } from '@/lib/api'
import { useRepository } from '@/context/repository-context'

interface Repository {
  id: number
  name: string
  source_type: 'github' | 'zip'
  repo_url: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  file_count?: number
  line_count?: number
}

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(false)
  const [githubUrl, setGithubUrl] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { activeRepo, setActiveRepo } = useRepository()

  // Load repositories on mount
  useEffect(() => {
    loadRepositories()
  }, [])

  async function loadRepositories() {
    const result = await getUserRepositories()
    if (result.error) {
      setError(result.error)
    } else if (result.data) {
      // Auto-select the first repository if none is selected
      if (!activeRepo && result.data.repositories && result.data.repositories.length > 0) {
        setActiveRepo(result.data.repositories[0])
      }
      setRepositories(result.data.repositories || [])
    }
  }

  async function handleGitHubSubmit() {
    if (!githubUrl.trim()) {
      setError('Please enter a GitHub URL')
      return
    }

    // Check authentication
    if (!isAuthenticated()) {
      setError('Please log in to submit repositories')
      setTimeout(() => router.push('/login'), 2000)
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    console.log('[REPOSITORIES] Submitting GitHub repo:', githubUrl)
    const result = await submitGitHubRepo(githubUrl)
    
    if (result.error) {
      console.error('[REPOSITORIES] Error submitting GitHub repo:', result.error)
      
      // Check for authentication errors
      if (result.error.includes('Unauthorized') || result.error.includes('401')) {
        setError('Session expired. Please log in again.')
        setTimeout(() => router.push('/login'), 2000)
      } else {
        setError(result.error)
      }
    } else {
      console.log('[REPOSITORIES] GitHub repo submitted successfully')
      setSuccess('Repository submitted for scanning!')
      setGithubUrl('')
      await loadRepositories()
    }

    setLoading(false)
  }

  async function handleFileUpload() {
    if (!uploadFile) {
      setError('Please select a ZIP file')
      return
    }

    if (!uploadFile.name.endsWith('.zip')) {
      setError('Only ZIP files are supported')
      return
    }

    // Check authentication
    if (!isAuthenticated()) {
      setError('Please log in to upload files')
      setTimeout(() => router.push('/login'), 2000)
      return
    }

    // Check file size (100MB limit)
    const maxSize = 100 * 1024 * 1024
    if (uploadFile.size > maxSize) {
      setError('File size exceeds 100MB limit')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    console.log('[REPOSITORIES] Uploading ZIP file:', uploadFile.name)
    const result = await uploadZipFile(uploadFile)
    
    if (result.error) {
      console.error('[REPOSITORIES] Error uploading ZIP:', result.error)
      
      // Check for authentication errors
      if (result.error.includes('Unauthorized') || result.error.includes('401')) {
        setError('Session expired. Please log in again.')
        setTimeout(() => router.push('/login'), 2000)
      } else {
        setError(result.error)
      }
    } else {
      console.log('[REPOSITORIES] ZIP file uploaded successfully')
      setSuccess('ZIP file uploaded and submitted for scanning!')
      setUploadFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      await loadRepositories()
    }

    setLoading(false)
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this repository?')) {
      return
    }

    const result = await deleteRepository(id)
    
    if (result.error) {
      setError(result.error)
    } else {
      setSuccess('Repository deleted')
      await loadRepositories()
    }
  }

  function getStatusIcon(status: Repository['status']) {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-yellow-400" />
    }
  }

  function getStatusColor(status: Repository['status']) {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400'
      case 'failed':
        return 'bg-red-500/20 text-red-400'
      case 'processing':
        return 'bg-blue-500/20 text-blue-400'
      default:
        return 'bg-yellow-500/20 text-yellow-400'
    }
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Repository Onboarding</h1>
          <p className="text-muted-foreground">Connect your GitHub repository or upload a ZIP file</p>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
          {error}
        </div>
      )}
      {success && (
        <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400">
          {success}
        </div>
      )}

      {/* GitHub Connection Card */}
      <Card className="p-8 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-primary" />
          Connect GitHub Repository
        </h3>
        <div className="space-y-4">
          <input
            type="text"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="GitHub repository URL (e.g., https://github.com/user/repo)"
            className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={loading}
          />
          <div className="flex gap-3">
            <Button 
              onClick={handleGitHubSubmit}
              disabled={loading || !githubUrl.trim()}
              className="bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : (
                'Connect'
              )}
            </Button>
            <Button 
              onClick={() => setGithubUrl('')}
              className="bg-secondary hover:bg-secondary/80 text-foreground border border-border"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Card>

      {/* ZIP Upload Card */}
      <Card className="p-8 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-primary" />
          Or Upload ZIP File
        </h3>
        <div 
          className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-primary transition-colors cursor-pointer"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-sm text-foreground mb-2">
            {uploadFile ? uploadFile.name : 'Drag and drop your codebase ZIP'}
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            or click to browse (max 100MB)
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            className="hidden"
            disabled={loading}
          />
          <Button 
            onClick={(e) => {
              e.stopPropagation()
              if (uploadFile) {
                handleFileUpload()
              } else {
                fileInputRef.current?.click()
              }
            }}
            disabled={loading}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : uploadFile ? (
              'Upload & Scan'
            ) : (
              'Select File'
            )}
          </Button>
        </div>
      </Card>

      {/* Connected Repositories */}
      <Card className="p-8 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-6">Your Repositories</h3>
        {repositories.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">
            No repositories yet. Add one above to get started!
          </p>
        ) : (
          <div className="space-y-3">
            {repositories.map((repo) => (
              <div 
                key={repo.id} 
                onClick={() => setActiveRepo(repo)}
                className={`flex items-center justify-between p-4 rounded-lg border transition-all cursor-pointer ${
                  activeRepo?.id === repo.id 
                    ? 'bg-primary/10 border-primary shadow-md' 
                    : 'bg-secondary/50 border-border/50 hover:bg-secondary/80 hover:border-border'
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {getStatusIcon(repo.status)}
                    <p className="text-sm font-medium text-foreground">{repo.name}</p>
                    {activeRepo?.id === repo.id && (
                      <span className="text-xs px-2 py-0.5 rounded bg-primary/20 text-primary">
                        Selected
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {repo.file_count && repo.line_count ? (
                      `${repo.file_count.toLocaleString()} files • ${repo.line_count.toLocaleString()} lines`
                    ) : (
                      `Added ${new Date(repo.created_at).toLocaleDateString()}`
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded text-xs font-medium ${getStatusColor(repo.status)}`}>
                    {repo.status}
                  </span>
                  <Button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(repo.id)
                    }}
                    variant="ghost"
                    size="sm"
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
