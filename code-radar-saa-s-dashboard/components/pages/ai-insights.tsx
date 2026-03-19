'use client'

import React, { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Send, Sparkles, Code2 } from 'lucide-react'

export default function AIInsightsPage() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Array<{ type: 'user' | 'assistant'; content: string; files?: string[] }>>([
    {
      type: 'assistant',
      content: 'Hello! I\'m CodeRadar\'s AI assistant. Ask me questions about your codebase analysis, architecture recommendations, or technical debt. I can help you understand code complexity, find optimization opportunities, and suggest refactoring strategies.',
    },
  ])

  const handleSend = () => {
    if (question.trim()) {
      setMessages([
        ...messages,
        { type: 'user', content: question },
        {
          type: 'assistant',
          content: 'Based on my analysis, I found several opportunities to improve your code complexity score. The main bottleneck is in your API middleware layer where you have deep nesting that could be extracted into separate functions. I also noticed duplicate logic in your store modules that could be consolidated.',
          files: ['apps/web/middleware.ts', 'lib/store/index.ts', 'packages/core/api.ts'],
        },
      ])
      setQuestion('')
    }
  }

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">AI Insights</h1>
        <p className="text-muted-foreground">Ask natural language questions about your codebase</p>
      </div>

      {/* Chat Container */}
      <Card className="p-6 border-border bg-card h-96 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-md px-4 py-3 rounded-lg ${
                  msg.type === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-foreground border border-border'
                }`}
              >
                {msg.type === 'assistant' && (
                  <div className="flex items-start gap-2 mb-2">
                    <Sparkles className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span className="text-xs font-semibold">AI Assistant</span>
                  </div>
                )}
                <p className="text-sm">{msg.content}</p>
                {msg.files && msg.files.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border/30 space-y-1">
                    <p className="text-xs font-semibold text-muted-foreground">Cited files:</p>
                    {msg.files.map((file, fidx) => (
                      <div key={fidx} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
                        <Code2 className="w-3 h-3" />
                        {file}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your code..."
            className="flex-1 px-4 py-2 rounded-lg bg-secondary border border-border text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <Button
            onClick={handleSend}
            className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </Card>

      {/* Suggested Questions */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-4">Suggested Questions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            'What files have the highest complexity?',
            'How can I reduce technical debt?',
            'What are the main architectural concerns?',
            'Which functions should I refactor first?',
            'Are there circular dependencies?',
            'What patterns are duplicated across files?',
          ].map((q, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuestion(q)
                setTimeout(() => handleSend(), 100)
              }}
              className="text-left px-4 py-3 rounded-lg bg-secondary border border-border text-foreground hover:border-primary transition-colors text-sm"
            >
              {q}
            </button>
          ))}
        </div>
      </Card>

      {/* Confidence Indicator */}
      <Card className="p-6 border-border bg-card">
        <h3 className="text-lg font-semibold text-foreground mb-4">Analysis Confidence</h3>
        <div className="space-y-4">
          {[
            { category: 'Code Complexity', confidence: 95 },
            { category: 'Dependency Analysis', confidence: 88 },
            { category: 'Duplication Detection', confidence: 92 },
            { category: 'Best Practice Adherence', confidence: 78 },
          ].map((item, idx) => (
            <div key={idx}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-foreground font-medium">{item.category}</p>
                <span className="text-sm font-semibold text-primary">{item.confidence}%</span>
              </div>
              <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${item.confidence}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
