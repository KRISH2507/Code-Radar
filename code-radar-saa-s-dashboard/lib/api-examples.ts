// Example: Making authenticated API calls in your components

import { fetchAPI } from '@/lib/api'

/**
 * Example 1: Fetch user repositories
 */
export async function getUserRepositories() {
  const { data, error } = await fetchAPI('/api/repositories')
  
  if (error) {
    console.error('Failed to fetch repositories:', error)
    return []
  }
  
  return data
}

/**
 * Example 2: Create a new repository scan
 */
export async function createScan(repositoryUrl: string) {
  const { data, error } = await fetchAPI('/api/scans', {
    method: 'POST',
    body: JSON.stringify({
      repository_url: repositoryUrl,
    }),
  })
  
  if (error) {
    throw new Error(error)
  }
  
  return data
}

/**
 * Example 3: Get scan results
 */
export async function getScanResults(scanId: string) {
  const { data, error } = await fetchAPI(`/api/scans/${scanId}`)
  
  if (error) {
    throw new Error(error)
  }
  
  return data
}

/**
 * Example 4: Update user settings
 */
export async function updateUserSettings(settings: any) {
  const { data, error } = await fetchAPI('/api/user/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
  
  if (error) {
    throw new Error(error)
  }
  
  return data
}

/**
 * Example usage in a React component:
 * 
 * ```tsx
 * 'use client'
 * 
 * import { useEffect, useState } from 'react'
 * import { getUserRepositories } from '@/lib/api-examples'
 * 
 * export default function RepositoriesPage() {
 *   const [repos, setRepos] = useState([])
 *   const [loading, setLoading] = useState(true)
 *   
 *   useEffect(() => {
 *     async function loadRepos() {
 *       const data = await getUserRepositories()
 *       setRepos(data)
 *       setLoading(false)
 *     }
 *     
 *     loadRepos()
 *   }, [])
 *   
 *   if (loading) return <div>Loading...</div>
 *   
 *   return (
 *     <div>
 *       {repos.map(repo => (
 *         <div key={repo.id}>{repo.name}</div>
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */
