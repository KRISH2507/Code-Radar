import React from "react"
import type { Metadata } from 'next'
import { IBM_Plex_Mono, Space_Grotesk, Syne } from 'next/font/google'
import { ThemeProvider } from '@/context/theme-context'
import { RepositoryProvider } from '@/context/repository-context'
import { UserProvider } from '@/context/user-context'

import './globals.css'

const _spaceGrotesk = Space_Grotesk({ subsets: ['latin'], weight: ['400', '500', '600', '700'] })
const _ibmPlexMono = IBM_Plex_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] })
const _syne = Syne({ subsets: ['latin'], weight: ['400', '500', '600', '700'] })

export const metadata: Metadata = {
  title: 'CodeRadar - Code Analysis Dashboard',
  description: 'Analyze codebases, detect architectural risks, and measure technical debt',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${_spaceGrotesk.className} antialiased bg-background text-foreground`}>
        <ThemeProvider>
          <UserProvider>
            <RepositoryProvider>
              {children}
            </RepositoryProvider>
          </UserProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
