'use client'

import React from 'react'
import { useUser } from '@/context/user-context'

export default function PlanBadge() {
    const { user, loading } = useUser()

    if (loading || !user) return null

    const isPro = user.plan === 'pro'

    return (
        <span
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '2px 10px',
                borderRadius: '9999px',
                fontSize: '11px',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                border: '1px solid',
                ...(isPro
                    ? {
                        background: 'linear-gradient(135deg, #f59e0b22, #d9770622)',
                        borderColor: '#f59e0b66',
                        color: '#f59e0b',
                    }
                    : {
                        background: 'linear-gradient(135deg, #3b82f622, #1d4ed822)',
                        borderColor: '#3b82f666',
                        color: '#60a5fa',
                    }),
            }}
        >
            {isPro ? '⚡ Pro' : 'Free'}
        </span>
    )
}
