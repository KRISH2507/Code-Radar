'use client'

import React, { useEffect, useState, useRef } from 'react'
import { ArrowRight, Github, Zap, Shield, TrendingUp, Code2, Cpu, GitBranch, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import LandingNav from '@/components/landing-nav'

interface LandingPageProps {
  onNavigateToDashboard?: () => void
}

export default function LandingPage({ onNavigateToDashboard }: LandingPageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const radarRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setIsLoaded(true)
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY })
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const features = [
    {
      icon: Code2,
      title: 'Deep Analysis',
      description: 'Scan your codebase detecting complexity and architectural patterns',
    },
    {
      icon: Cpu,
      title: 'Risk Detection',
      description: 'Identify high-risk files and technical debt automatically',
    },
    {
      icon: TrendingUp,
      title: 'Trend Monitoring',
      description: 'Track codebase health over time with detailed metrics',
    },
    {
      icon: Shield,
      title: 'Impact Simulation',
      description: 'Simulate refactoring impact across your architecture',
    },
    {
      icon: Zap,
      title: 'AI Insights',
      description: 'Get AI-powered recommendations to resolve issues',
    },
    {
      icon: GitBranch,
      title: 'Multi-Repo Support',
      description: 'Analyze multiple repositories simultaneously',
    },
  ]

  return (
    <div className="relative min-h-screen w-full bg-background text-foreground overflow-x-hidden overflow-y-auto">
      <LandingNav onNavigateToDashboard={onNavigateToDashboard} />

      {/* Animated background elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute top-20 right-1/4 w-80 h-80 rounded-full bg-gradient-to-br from-primary/30 to-transparent blur-3xl animate-parallax-drift"></div>
        <div className="absolute bottom-32 left-1/3 w-96 h-96 rounded-full bg-gradient-to-tr from-blue-500/20 to-transparent blur-3xl animate-parallax-drift" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 right-0 w-72 h-72 rounded-full bg-gradient-to-l from-cyan-500/20 to-transparent blur-3xl animate-parallax-drift" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Grid overlay */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]">
        <svg className="w-full h-full" width="100%" height="100%">
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="currentColor" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>



      {/* Hero Section - Immersive 3D */}
      <section className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 py-32 pt-40">
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {/* Radar visualization */}
          <div 
            ref={radarRef}
            className="relative w-96 h-96 animate-radar-spin opacity-10"
          >
            <div className="absolute inset-0 border border-primary/50 rounded-full"></div>
            <div className="absolute inset-12 border border-primary/40 rounded-full"></div>
            <div className="absolute inset-24 border border-primary/30 rounded-full"></div>
            <div className="absolute inset-32 border border-primary/20 rounded-full"></div>
          </div>
        </div>

        <div className="relative z-10 text-center max-w-4xl space-y-8 animate-fadeInUp">
          {/* Main headline */}
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-tight">
            Radar
            <span className="block text-transparent bg-gradient-to-r from-primary via-blue-500 to-cyan-400 bg-clip-text animate-gradient-shift bg-[200%] bg-left">
              Your Code
            </span>
          </h1>

          {/* Subheading */}
          <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Discover architectural risks, measure technical debt, and receive AI-powered recommendations. CodeRadar transforms your codebase into actionable intelligence.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
            <Button 
              onClick={() => window.location.href = '/signup'}
              className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-700 text-primary-foreground border-0 shadow-lg shadow-primary/40 font-medium px-8 py-6 text-lg rounded-full group"
            >
              Sign Up
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition" />
            </Button>
            <Button 
              onClick={() => window.location.href = '/login'}
              variant="outline" 
              className="px-8 py-6 text-lg rounded-full font-medium border-border/50 hover:bg-secondary/50 bg-transparent"
            >
              Login
            </Button>
          </div>
        </div>

        {/* Floating code blocks - 3D inspired */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-card border border-border/50 rounded-lg p-3 backdrop-blur-sm animate-float opacity-40 font-mono text-xs text-muted-foreground">
            {'<dependency>'}
          </div>
          <div className="absolute top-1/3 right-1/4 w-40 h-24 bg-card border border-border/50 rounded-lg p-4 backdrop-blur-sm animate-float opacity-40 font-mono text-xs text-muted-foreground" style={{ animationDelay: '1s' }}>
            complexity: 42%
          </div>
          <div className="absolute bottom-1/4 left-1/3 w-36 h-28 bg-card border border-border/50 rounded-lg p-3 backdrop-blur-sm animate-float opacity-40 font-mono text-xs text-muted-foreground" style={{ animationDelay: '2s' }}>
            risk_score: 8/10
          </div>
        </div>
      </section>

      {/* Capability Discovery Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-32 space-y-16">
        <div className="text-center space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            Capabilities
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything to maintain code excellence and architectural integrity
          </p>
        </div>

        {/* Asymmetric feature layout */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <div
                key={idx}
                className="group relative p-6 rounded-xl border border-border/50 bg-card/40 hover:bg-card/60 backdrop-blur-sm transition-all duration-300 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/20 transform hover:-translate-y-2 overflow-hidden"
                style={{
                  opacity: 0,
                  animation: isLoaded ? `fadeInUp 0.6s ease-out ${0.2 + idx * 0.1}s forwards` : 'none'
                }}
              >
                {/* Glow on hover */}
                <div className="absolute -inset-px bg-gradient-to-r from-primary/0 via-primary/20 to-blue-600/0 rounded-xl opacity-0 group-hover:opacity-100 blur transition-opacity duration-300 -z-10"></div>

                <div className="p-3 w-fit bg-primary/10 rounded-lg mb-4 border border-primary/20 group-hover:border-primary/50 transition-colors">
                  <Icon className="w-6 h-6 text-primary" />
                </div>

                <h3 className="font-bold text-lg mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Stats Section - Represented as nodes */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-32">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { value: '45K+', label: 'Codebases' },
            { value: '98%', label: 'Accuracy' },
            { value: '2.3s', label: 'Avg Scan' },
            { value: '87%', label: 'Satisfaction' },
          ].map((stat, idx) => (
            <div
              key={idx}
              className="p-6 rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm hover:border-primary/50 transition-colors text-center"
              style={{
                opacity: 0,
                animation: isLoaded ? `fadeInUp 0.6s ease-out ${0.4 + idx * 0.1}s forwards` : 'none'
              }}
            >
              <div className="text-3xl md:text-4xl font-bold text-transparent bg-gradient-to-r from-primary to-blue-600 bg-clip-text">
                {stat.value}
              </div>
              <p className="text-muted-foreground text-sm mt-2">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA - Full screen experience */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 py-32">
        <div className="rounded-2xl border border-primary/30 bg-gradient-to-br from-primary/10 to-blue-600/10 backdrop-blur-sm p-12 text-center space-y-8 relative overflow-hidden">
          {/* Background glow */}
          <div className="absolute -inset-px bg-gradient-to-r from-primary/0 via-primary/10 to-blue-600/0 rounded-2xl -z-10 blur-xl"></div>

          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            See Your Code Through New Eyes
          </h2>
          <p className="text-lg text-muted-foreground">
            Join engineering teams transforming how they understand and maintain code.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              onClick={() => window.location.href = '/signup'}
              className="bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-700 text-primary-foreground border-0 shadow-lg shadow-primary/40 font-medium px-8 py-6 text-lg rounded-full group"
            >
              Get Started
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition" />
            </Button>
            <p className="text-sm text-muted-foreground">14-day free trial. No credit card.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/50 backdrop-blur-sm bg-background/50 py-12 mt-32">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-blue-600 rounded-lg flex items-center justify-center font-bold text-sm text-primary-foreground">
                ◈
              </div>
              <span className="font-bold">CodeRadar</span>
            </div>
            <div className="flex items-center gap-8 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground transition">Privacy</a>
              <a href="#" className="hover:text-foreground transition">Terms</a>
              <a href="#" className="hover:text-foreground transition">Docs</a>
              <a href="#" className="hover:text-foreground transition">Contact</a>
            </div>
            <p className="text-sm text-muted-foreground">© 2025 CodeRadar</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
